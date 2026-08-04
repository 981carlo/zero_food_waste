from django.urls import path

from . import views


app_name = "despensa"

urlpatterns = [
    path("alimentos/", views.listado_alimentos_web, name="listado_alimentos"),
    path("alimentos/nuevo/", views.alta_alimento_web, name="alta_alimento"),
]