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
    
    unidad_medida = forms.ChoiceField(
        choices=[("", "Selecciona una unidad")] + list(Alimento.UnidadMedida.choices),
        label="Unidad de medida",
        required=True,
    )
    
    nombre = forms.CharField(
        max_length=50,
        label="Nombre",
        error_messages={
            "required": "Este campo es requerido.",
            "max_length": "El nombre no puede tener más de 50 caracteres.",
        },
    )
    
    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()

        return nombre[:1].upper() + nombre[1:]
    
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
        widgets = {
            "cantidad": forms.NumberInput(
                attrs={
                    "step": "1",
                    "min": "0",
                }
            ),
        }
