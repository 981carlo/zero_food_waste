from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Alimento
from .serializers import AlimentoSerializer


class AlimentoViewSet(viewsets.ModelViewSet):
    serializer_class = AlimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alimento.objects.filter(
            usuario=self.request.user
        ).order_by("fecha_caducidad")

    def perform_create(self, serializer):
        serializer.save(
            usuario=self.request.user
        )
