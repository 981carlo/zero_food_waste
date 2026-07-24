from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


Usuario = get_user_model()


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = Usuario
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )
        extra_kwargs = {
            "email": {
                "required": True,
                "allow_blank": False,
            },
        }

    def validate_email(self, email):
        email = email.strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Ya existe una cuenta con este correo electrónico."
            )

        return email

    def validate(self, datos):
        password1 = datos.get("password1")
        password2 = datos.get("password2")

        if password1 != password2:
            raise serializers.ValidationError(
                {
                    "password2": (
                        "Las contraseñas no coinciden."
                    )
                }
            )

        usuario = Usuario(
            username=datos.get("username"),
            email=datos.get("email"),
        )

        try:
            validate_password(password1, user=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {
                    "password1": list(error.messages),
                }
            ) from error

        return datos

    def create(self, validated_data):
        password = validated_data.pop("password1")
        validated_data.pop("password2")

        return Usuario.objects.create_user(
            password=password,
            **validated_data,
        )
        
class InicioSesionSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    password = serializers.CharField(
        required=True,
        allow_blank=False,
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, datos):
        usuario = authenticate(
            request=self.context.get("request"),
            username=datos["username"].strip(),
            password=datos["password"],
        )

        if usuario is None:
            raise serializers.ValidationError(
                "Credenciales incorrectas."
            )

        datos["usuario"] = usuario

        return datos