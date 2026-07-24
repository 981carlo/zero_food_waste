from django.contrib.auth import authenticate, login, logout
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
    
@require_POST
def iniciar_sesion(request):
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    if not username or not password:
        return JsonResponse(
            {
                "error": (
                    "El nombre de usuario y la contraseña son obligatorios."
                )
            },
            status=400,
        )

    usuario = authenticate(
        request,
        username=username,
        password=password,
    )

    if usuario is None:
        return JsonResponse(
            {"error": "Credenciales incorrectas."},
            status=401,
        )

    login(request, usuario)

    return JsonResponse(
        {
            "mensaje": "Sesión iniciada correctamente.",
            "usuario": {
                "username": usuario.username,
                "email": usuario.email,
            },
        },
        status=200,
    )


@require_POST
def cerrar_sesion(request):
    logout(request)

    return JsonResponse(
        {"mensaje": "Sesión cerrada correctamente."},
        status=200,
    )