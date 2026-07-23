from django.contrib import admin

from .models import Alimento


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "cantidad",
        "unidad_medida",
        "fecha_caducidad_formateada",
        "usuario",
    )
    search_fields = ("nombre", "usuario__username")
    list_filter = ("unidad_medida", "fecha_caducidad")
    ordering = ("fecha_caducidad",)

    @admin.display(
        ordering="fecha_caducidad",
        description="Fecha de caducidad",
    )
    def fecha_caducidad_formateada(self, obj):
        return obj.fecha_caducidad.strftime("%d/%m/%Y")