from django.urls import path

from . import api_views


app_name = "usuarios_api"

urlpatterns = [
    path("registro/", api_views.RegistroUsuarioAPIView.as_view(), name="registro"),
    path("iniciar-sesion/", api_views.InicioSesionAPIView.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", api_views.CerrarSesionAPIView.as_view(), name="cerrar_sesion"),
]