from django.conf import settings
from django.db import models


class Alimento(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alimentos",
    )
    nombre = models.CharField(max_length=100)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2)
    unidad_medida = models.CharField(max_length=20)
    fecha_caducidad = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre
