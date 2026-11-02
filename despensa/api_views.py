from datetime import timedelta

from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alimento
from .serializers import AlimentoSerializer, GenerarRecetaSerializer
from .services import generar_receta_con_llm, ErrorGeneracionReceta


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
        serializer = GenerarRecetaSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        alimentos = Alimento.objects.filter(
            usuario=request.user,
            fecha_caducidad__gte=timezone.localdate(),
        ).order_by("fecha_caducidad")

        ids = serializer.validated_data["alimentos_seleccionados"]
        indicaciones = serializer.validated_data["indicaciones_usuario"]

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
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            resultado,
            status=status.HTTP_200_OK,
        )