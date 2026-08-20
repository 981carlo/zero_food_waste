import os
from datetime import timedelta

from django.utils import timezone
from google import genai


def formatear_cantidad(cantidad):
    if cantidad == cantidad.to_integral():
        return str(int(cantidad))

    return str(cantidad).replace(".", ",")


def construir_prompt_recetas(alimentos, usar_todos_los_alimentos=False):
    hoy = timezone.localdate()
    limite_proximos = hoy + timedelta(days=7)

    lineas_alimentos = []

    for alimento in alimentos:
        fecha_caducidad = alimento.fecha_caducidad

        if hoy <= fecha_caducidad <= limite_proximos:
            prioridad = "prioritario por caducidad próxima"
        else:
            prioridad = "no prioritario"

        lineas_alimentos.append(
            f"- {alimento.nombre}: "
            f"{formatear_cantidad(alimento.cantidad)} {alimento.unidad_medida}, "
            f"caduca el {fecha_caducidad.isoformat()} "
            f"({prioridad})"
        )

    lista_alimentos = "\n".join(lineas_alimentos)

    if usar_todos_los_alimentos:
        instruccion_uso_alimentos = (
            "- Debes utilizar todos los alimentos de la lista, porque han sido seleccionados por el usuario."
        )
    else:
        instruccion_uso_alimentos = (
            "- No es necesario utilizar todos los alimentos de la lista; selecciona solo los que encajen bien en una receta coherente."
        )
    return f"""
Eres un asistente culinario para una aplicación web orientada a reducir el desperdicio alimentario doméstico.

Tu tarea es proponer una receta sencilla a partir de los alimentos disponibles del usuario.

Fecha actual: {hoy.isoformat()}

Alimentos disponibles:
{lista_alimentos}

Instrucciones:
- Responde siempre en español.
- Prioriza los alimentos marcados como prioritarios por caducidad próxima.
- {instruccion_uso_alimentos}
- Propón una receta realista y sencilla.
- No inventes ingredientes principales que no estén en la lista.
- Puedes asumir ingredientes básicos de cocina como sal, aceite, agua o especias.
- Usa medidas lógicas, no pongas cosas como "7,25 gramos de sal". Pon la medida en redondeada y su equivalencia cuando proceda. Por ejemplo: "225 ml de leche o una taza"
- No uses formato Markdown.
- No uses almohadillas, asteriscos ni separadores con guiones.
- Usa texto plano, claro y fácil de mostrar en una página web.

Estructura de la respuesta:
1. Nombre de la receta
2. Alimentos utilizados
3. Ingredientes básicos adicionales, si hacen falta
4. Duración
5. Pasos de preparación
""".strip()


def generar_receta_con_llm(alimentos, usar_todos_los_alimentos=False):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        raise RuntimeError(
            "No se ha configurado GEMINI_API_KEY en el archivo .env"
        )

    prompt = construir_prompt_recetas(
        alimentos,
        usar_todos_los_alimentos=usar_todos_los_alimentos,
    )

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    return interaction.output_text