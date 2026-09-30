from decimal import Decimal, InvalidOperation

from .models import Alimento


def finalizar_receta(usuario, alimentos_utilizados):
    operaciones = []

    for alimento_utilizado in alimentos_utilizados:
        try:
            alimento = Alimento.objects.get(
                pk=alimento_utilizado["id"],
                usuario=usuario,
            )

            cantidad_utilizada = Decimal(
                str(alimento_utilizado["cantidad_utilizada"])
            )

        except (
            Alimento.DoesNotExist,
            KeyError,
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            return (
                False,
                "No se ha podido actualizar la despensa porque los datos de la receta no son válidos."
            )

        if cantidad_utilizada <= 0:
            return (
                False,
                "No se ha podido actualizar la despensa porque una de las cantidades no es válida."
            )

        if cantidad_utilizada > alimento.cantidad:
            return (
                False,
                f"No hay suficiente cantidad de {alimento.nombre} en la despensa."
            )

        operaciones.append(
            (alimento, cantidad_utilizada)
        )

    for alimento, cantidad_utilizada in operaciones:
        nueva_cantidad = alimento.cantidad - cantidad_utilizada

        if nueva_cantidad == 0:
            alimento.delete()
        else:
            alimento.cantidad = nueva_cantidad
            alimento.save()

    return (
        True,
        "Receta finalizada. La despensa se ha actualizado correctamente."
    )