from django import forms

from .models import Alimento


class AlimentoForm(forms.ModelForm):
    fecha_caducidad = forms.DateField(
        label="Fecha de caducidad",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"}
        ),
        input_formats=["%Y-%m-%d"],
    )
    
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
        }
