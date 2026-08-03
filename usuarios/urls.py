from django.urls import path

from . import views


app_name = "usuarios"

urlpatterns = [
    path("registro/", views.RegistroUsuarioAPIView.as_view(), name="registro"),
    path("iniciar-sesion/", views.InicioSesionAPIView.as_view(), name="iniciar_sesion"),
    path("cerrar-sesion/", views.CerrarSesionAPIView.as_view(), name="cerrar_sesion"),
    
    path("registro-web/", views.registro_web, name="registro_web"),
    path("login-web/", views.login_web, name="login_web"),
    path("logout-web/", views.logout_web, name="logout_web"),
]