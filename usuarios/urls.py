from django.urls import path

from . import views


app_name = "usuarios"

urlpatterns = [
    path("registro-web/", views.registro_web, name="registro_web"),
    path("login-web/", views.login_web, name="login_web"),
    path("logout-web/", views.logout_web, name="logout_web"),
]