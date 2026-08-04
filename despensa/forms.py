from django import forms

from .models import Alimento


class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = [
            "nombre",
            "cantidad",
            "unidad_medida",
            "fecha_caducidad",
        ]
        labels = {
            "nombre": "Nombre",
            "cantidad": "Cantidad",
            "unidad_medida": "Unidad de medida",
            "fecha_caducidad": "Fecha de caducidad",
        }
        widgets = {
            "fecha_caducidad": forms.DateInput(
                attrs={"type": "date"}
            ),
        }