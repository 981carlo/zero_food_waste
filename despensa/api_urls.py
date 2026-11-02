from rest_framework.routers import DefaultRouter

from .api_views import AlimentoViewSet


router = DefaultRouter()

router.register("alimentos", AlimentoViewSet, basename="alimento",)

urlpatterns = router.urls