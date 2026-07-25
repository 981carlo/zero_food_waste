from rest_framework import serializers

from .models import Alimento


class AlimentoSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Alimento
        fields = (
            "id",
            "nombre",
            "cantidad",
            "unidad_medida",
            "fecha_caducidad",
            "fecha_creacion",
            "fecha_actualizacion",
        )
        read_only_fields = (
            "fecha_creacion",
            "fecha_actualizacion",
        )