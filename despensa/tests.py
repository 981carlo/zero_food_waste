from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Alimento
from .recipes import finalizar_receta


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
    # Comprueba que un usuario no puede acceder a un alimento perteneciente a otro usuario.
    def test_usuario_no_puede_acceder_a_alimento_ajeno(self):
        self.client.force_authenticate(user=self.usuario_ajeno)

        url = reverse(
            "alimento-detail",
            args=[self.alimento.pk]
        )

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, 404)


class RecetaFinalizacionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="usuario_receta",
            password="Password123!"
        )

        self.alimento = Alimento.objects.create(
            usuario=self.usuario,
            nombre="Arroz",
            cantidad="1.00",
            unidad_medida="kilogramos",
            fecha_caducidad=date(2026, 10, 15),
        )

    # Comprueba que al finalizar una receta se descuenta la cantidad utilizada.
    def test_finalizar_receta_descuenta_cantidad_utilizada(self):
        alimentos_utilizados = [
            {
                "id": str(self.alimento.pk),
                "cantidad_utilizada": "0.25",
            }
        ]

        resultado, _ = finalizar_receta(
            self.usuario,
            alimentos_utilizados
        )

        self.alimento.refresh_from_db()

        self.assertTrue(resultado)
        self.assertEqual(
            self.alimento.cantidad,
            Decimal("0.75")
        )

    # Comprueba que el alimento se elimina cuando se utiliza toda la cantidad disponible.
    def test_finalizar_receta_elimina_alimento_si_cantidad_llega_a_cero(self):
        alimentos_utilizados = [
            {
                "id": str(self.alimento.pk),
                "cantidad_utilizada": "1.00",
            }
        ]

        resultado, _ = finalizar_receta(
            self.usuario,
            alimentos_utilizados
        )

        self.assertTrue(resultado)
        self.assertFalse(
            Alimento.objects.filter(pk=self.alimento.pk).exists()
        )

    # Comprueba que no se actualiza ningún alimento si una cantidad es insuficiente.
    def test_finalizar_receta_no_realiza_actualizaciones_parciales(self):
        segundo_alimento = Alimento.objects.create(
            usuario=self.usuario,
            nombre="Leche",
            cantidad="0.50",
            unidad_medida="litros",
            fecha_caducidad=date(2026, 10, 12),
        )

        alimentos_utilizados = [
            {
                "id": str(self.alimento.pk),
                "cantidad_utilizada": "0.25",
            },
            {
                "id": str(segundo_alimento.pk),
                "cantidad_utilizada": "1.00",
            },
        ]

        resultado, _ = finalizar_receta(
            self.usuario,
            alimentos_utilizados
        )

        self.alimento.refresh_from_db()
        segundo_alimento.refresh_from_db()

        self.assertFalse(resultado)
        self.assertEqual(
            self.alimento.cantidad,
            Decimal("1.00")
        )
        self.assertEqual(
            segundo_alimento.cantidad,
            Decimal("0.50")
        )
