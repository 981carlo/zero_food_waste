from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


Usuario = get_user_model()


class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo electrónico."
            )

        return email