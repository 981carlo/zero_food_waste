from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import RegistroUsuarioForm

        
def registro_web(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            # Inicia sesión automáticamente después de crear correctamente la cuenta.
            login(request, usuario)
            messages.success(request, "Cuenta creada correctamente. Has iniciado sesión.")
            return redirect("inicio")
        
        messages.error(request, "No se ha podido crear la cuenta. Revisa los datos introducidos.")
    
    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})


def login_web(request):
    # Muestra un aviso cuando el usuario llega al login desde una vista protegida.
    if request.method == "GET" and request.GET.get("next"):
        messages.info(
            request,
            "Tu sesión ha finalizado o necesitas iniciar sesión para acceder a esta página."
        )

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Has iniciado sesión correctamente.")
            return redirect("inicio")
    else:
        form = AuthenticationForm()

    return render(request, "usuarios/login.html", {"form": form})

def logout_web(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente.")
        return redirect("inicio")

    return render(request, "usuarios/logout.html")