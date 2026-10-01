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

    # Añade una opción vacía para obligar al usuario a seleccionar una unidad.
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

        # Normaliza el nombre eliminando espacios y poniendo en mayúscula la primera letra.
        return nombre[:1].upper() + nombre[1:]

    def clean(self):
        cleaned_data = super().clean()

        cantidad = cleaned_data.get("cantidad")
        unidad_medida = cleaned_data.get("unidad_medida")

        if cantidad is None or not unidad_medida:
            return cleaned_data

        if cantidad <= 0:
            self.add_error(
                "cantidad",
                "La cantidad debe ser mayor que cero."
            )

        elif (
            unidad_medida in {
                Alimento.UnidadMedida.GRAMOS,
                Alimento.UnidadMedida.MILILITROS,
            }
            and cantidad != cantidad.to_integral()
        ):
            self.add_error(
                "cantidad",
                "La cantidad debe ser un número entero para esta unidad de medida."
            )

        return cleaned_data
    
    class Meta:
        model = Alimento
        fields = [
            "nombre",
            "unidad_medida",
            "cantidad",
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
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }
