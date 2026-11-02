from datetime import timedelta

from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alimento
from .serializers import AlimentoSerializer, GenerarRecetaSerializer, ModificarRecetaSerializer
from .recipes import finalizar_receta
from .services import generar_receta_con_llm, ErrorGeneracionReceta, modificar_receta_con_llm


class AlimentoViewSet(viewsets.ModelViewSet):
    serializer_class = AlimentoSerializer
    permission_classes = [IsAuthenticated]

    # Filtra los alimentos para que cada usuario solo acceda a los suyos.
    def get_queryset(self):
        return Alimento.objects.filter(
            usuario=self.request.user
        ).order_by("fecha_caducidad")

    # Asocia automáticamente cada nuevo alimento al usuario autenticado.
    def perform_create(self, serializer):
        serializer.save(
            usuario=self.request.user
        )

    @action(detail=False, methods=["get"], url_path="proximos")
    def proximos(self, request):
        hoy = timezone.localdate()
        limite = hoy + timedelta(days=7)

        # Devuelve únicamente los alimentos que caducan entre hoy y los próximos siete días.
        alimentos = self.get_queryset().filter(
            fecha_caducidad__gte=hoy,
            fecha_caducidad__lte=limite
        )

        serializer = self.get_serializer(alimentos, many=True)
        return Response(serializer.data)
    
    
class GenerarRecetaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Valida la selección de alimentos y las indicaciones del usuario.
        serializer = GenerarRecetaSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        # Obtiene únicamente los alimentos del usuario que no han caducado.
        alimentos = Alimento.objects.filter(
            usuario=request.user,
            fecha_caducidad__gte=timezone.localdate(),
        ).order_by("fecha_caducidad")

        ids = serializer.validated_data["alimentos_seleccionados"]
        indicaciones = serializer.validated_data["indicaciones_usuario"]

        # Si hay una selección, limita la generación a esos alimentos.
        # Sin selección, mantiene toda la despensa disponible.
        if ids:
            alimentos = alimentos.filter(pk__in=ids)

        if not alimentos.exists():
            return Response(
                {"detail": "No tienes alimentos disponibles para generar una receta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = generar_receta_con_llm(
                alimentos,
                usar_todos_los_alimentos=bool(ids),
                indicaciones_usuario=indicaciones,
            )
        except ErrorGeneracionReceta as error:
            # Devuelve el error sin sustituir la receta pendiente anterior.
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Guarda el texto y las cantidades para modificar o finalizar la receta.
        request.session["receta_pendiente_api"] = resultado

        return Response(
            resultado,
            status=status.HTTP_200_OK,
        )


class ModificarRecetaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Comprueba que el usuario ha proporcionado una indicación válida.
        serializer = ModificarRecetaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Recupera la última receta generada o modificada desde la API.
        receta_pendiente = request.session.get("receta_pendiente_api")

        if not receta_pendiente:
            return Response(
                {"detail": "No hay una receta pendiente para modificar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Permite utilizar cualquier alimento actual de la despensa sin caducar,
        # aunque no apareciera en la receta anterior.
        alimentos = Alimento.objects.filter(
            usuario=request.user,
            fecha_caducidad__gte=timezone.localdate(),
        ).order_by("fecha_caducidad")

        if not alimentos.exists():
            return Response(
                {"detail": "No tienes alimentos disponibles para modificar la receta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comentario = serializer.validated_data["comentario_usuario"]

        try:
            resultado = modificar_receta_con_llm(
                receta_pendiente["receta"],
                alimentos,
                comentario,
            )
        except ErrorGeneracionReceta as error:
            # Conserva la receta anterior si la modificación falla.
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Sustituye la receta pendiente y sus cantidades por la nueva versión.
        request.session["receta_pendiente_api"] = resultado

        return Response(
            resultado,
            status=status.HTTP_200_OK,
        )


class FinalizarRecetaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Recupera la última receta generada o modificada desde la API.
        receta_pendiente = request.session.get("receta_pendiente_api")

        if not receta_pendiente:
            return Response(
                {"detail": "No hay una receta pendiente para finalizar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alimentos_utilizados = receta_pendiente.get(
            "alimentos_utilizados",
            [],
        )

        if not alimentos_utilizados:
            return Response(
                {"detail": "La receta pendiente no contiene alimentos para descontar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Comprueba las cantidades actuales y actualiza la despensa.
        exito, mensaje = finalizar_receta(
            request.user,
            alimentos_utilizados,
        )

        if not exito:
            # Conserva la receta pendiente si no se ha podido finalizar.
            return Response(
                {"detail": mensaje},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Retira la receta de la sesión tras finalizar correctamente.
        request.session.pop("receta_pendiente_api", None)

        return Response(
            {"mensaje": mensaje},
            status=status.HTTP_200_OK,
        )