from rest_framework import serializers

from .models import Alimento


class AlimentoSerializer(serializers.ModelSerializer):
    # Representa el identificador ObjectId de MongoDB
    # como texto y evita que pueda modificarse.
    id = serializers.CharField(read_only=True)
    unidad_medida = serializers.ChoiceField(
        choices=Alimento.UnidadMedida.choices
    )
    
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

    def validate(self, datos):
        cantidad = datos.get(
            "cantidad",
            getattr(self.instance, "cantidad", None)
        )
        unidad_medida = datos.get(
            "unidad_medida",
            getattr(self.instance, "unidad_medida", None)
        )

        if cantidad is None or not unidad_medida:
            return datos

        if cantidad <= 0:
            raise serializers.ValidationError(
                {
                    "cantidad": "La cantidad debe ser mayor que cero."
                }
            )

        if (
            unidad_medida in {
                Alimento.UnidadMedida.GRAMOS,
                Alimento.UnidadMedida.MILILITROS,
            }
            and cantidad != cantidad.to_integral()
        ):
            raise serializers.ValidationError(
                {
                    "cantidad": "La cantidad debe ser un número entero para esta unidad de medida."
                }
            )

        return datos