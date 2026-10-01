from django.test import TestCase

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Alimento

# Comprueba que un usuario no puede acceder a un alimento perteneciente a otro usuario.
class AlimentoAislamientoTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.usuario_propietario = get_user_model().objects.create_user(
            username="usuario1",
            password="Password123!"
        )

        self.usuario_ajeno = get_user_model().objects.create_user(
            username="usuario2",
            password="Password123!"
        )

        self.alimento = Alimento.objects.create(
            usuario=self.usuario_propietario,
            nombre="Leche",
            cantidad="1.00",
            unidad_medida="litros",
            fecha_caducidad=date(2026, 10, 10),
        )

    def test_usuario_no_puede_acceder_a_alimento_ajeno(self):
        self.client.force_authenticate(user=self.usuario_ajeno)

        url = reverse(
            "alimento-detail",
            args=[self.alimento.pk]
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, 404)
