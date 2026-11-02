from datetime import timedelta

from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Alimento
from .serializers import AlimentoSerializer


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