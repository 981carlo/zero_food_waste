from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import RegistroUsuarioForm


@require_POST
def registrar_usuario(request):
    formulario = RegistroUsuarioForm(request.POST)

    if formulario.is_valid():
        usuario = formulario.save()

        return JsonResponse(
            {
                "mensaje": "Usuario registrado correctamente.",
                "usuario": {
                    "username": usuario.username,
                    "email": usuario.email,
                },
            },
            status=201,
        )

    return JsonResponse(
        {"errores": formulario.errors.get_json_data()},
        status=400,
    )