from django.urls import path

from . import views


app_name = "despensa"

urlpatterns = [
    path("alimentos/", views.listado_alimentos_web, name="listado_alimentos"),
    path("alimentos/nuevo/", views.alta_alimento_web, name="alta_alimento"),
    path("alimentos/<str:alimento_id>/editar/", views.editar_alimento_web, name="editar_alimento"),
    path("alimentos/<str:alimento_id>/eliminar/", views.eliminar_alimento_web, name="eliminar_alimento"),
    path("alimentos/proximos/", views.alimentos_proximos_web, name="alimentos_proximos"),
]