from rest_framework.routers import DefaultRouter

from django.urls import path

from .api_views import (
    AlimentoViewSet, 
    GenerarRecetaAPIView, 
    ModificarRecetaAPIView, 
    FinalizarRecetaAPIView,
)


router = DefaultRouter()

router.register("alimentos", AlimentoViewSet, basename="alimento",)

urlpatterns = [
    path("recetas/generar/", GenerarRecetaAPIView.as_view(), name="generar_receta"),
    path("recetas/modificar/", ModificarRecetaAPIView.as_view(), name="modificar_receta"),
    path("recetas/finalizar/", FinalizarRecetaAPIView.as_view(), name="finalizar_receta"),
] + router.urls