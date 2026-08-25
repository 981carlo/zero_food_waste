import os
from datetime import timedelta

from django.utils import timezone
from google import genai

class ErrorGeneracionReceta(Exception):
    pass


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
            "Debes utilizar todos los alimentos de la lista, porque han sido seleccionados por el usuario."
        )
    else:
        instruccion_uso_alimentos = (
            "No es necesario utilizar todos los alimentos de la lista; selecciona solo los que encajen bien en una receta coherente."
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
- Utiliza el punto 3 solo cuando sea necesario. De no ser necesario, el punto 4 pasa a ser el 3 y el punto 5 pasa a ser el 4
- Si detectas algo en la lista de alimentos que no sea un alimento, no lo incluyas en la receta. De ser así, añade un nuevo punto en la respuesta indicando qué elemento ha sido descartado por no ser un alimento

Estructura de la respuesta:
1. Nombre de la receta:
2. Alimentos utilizados:
3. Ingredientes básicos adicionales:
4. Duración:
5. Pasos de preparación:
""".strip()


def generar_receta_con_llm(alimentos, usar_todos_los_alimentos=False):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        raise ErrorGeneracionReceta(
            "No se ha podido generar la receta porque no está configurada la API del LLM."
        )

    prompt = construir_prompt_recetas(
        alimentos,
        usar_todos_los_alimentos=usar_todos_los_alimentos,
    )

    try:
        client = genai.Client(api_key=api_key)

        interaction = client.interactions.create(
            model=model,
            input=prompt,
        )

    except Exception as error:
        error_texto = str(error).lower()

        if (
            "quota" in error_texto
            or "too_many_requests" in error_texto
        ):
            raise ErrorGeneracionReceta(
                "Se ha alcanzado el límite temporal de consultas al LLM. Inténtalo de nuevo más tarde."
            )

        raise ErrorGeneracionReceta(
            "No se ha podido conectar con el servicio de generación de recetas. Inténtalo de nuevo más tarde."
        )

    receta = interaction.output_text

    if not receta or not receta.strip():
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta. Inténtalo de nuevo."
        )

    return receta


def construir_prompt_feedback_receta(receta_generada, alimentos_usados, comentario_usuario):
    alimentos_usados_texto = "\n".join(
        f"- {alimento.nombre}: {formatear_cantidad(alimento.cantidad)} {alimento.unidad_medida}"
        for alimento in alimentos_usados
    )
    return f"""
Eres un asistente culinario para una aplicación web orientada a reducir el desperdicio alimentario doméstico.

El usuario ya ha recibido esta receta:

{receta_generada}

El usuario ha elegido estos alimentos como alimentos principales permitidos:

{alimentos_usados_texto}

Ahora el usuario quiere modificarla con esta indicación:

{comentario_usuario}

Tu tarea es generar una nueva versión de la receta teniendo en cuenta la indicación del usuario.

Instrucciones:
- Responde siempre en español.
- Mantén una receta realista y sencilla.
- Respeta la intención del usuario.
- Mantén como alimentos principales únicamente los alimentos indicados en la lista anterior.
- No añadas alimentos principales nuevos que no estén en esa lista.
- No utilices otros alimentos de la despensa si no aparecen en la lista anterior.
- Solo puedes añadir ingredientes básicos habituales como agua, sal, aceite, especias o condimentos.
- No uses formato Markdown.
- No uses almohadillas, asteriscos ni separadores con guiones.
- Usa texto plano, claro y fácil de mostrar en una página web.
- Utiliza el punto 3 solo cuando sea necesario. De no ser necesario, el punto 4 pasa a ser el 3 y el punto 5 pasa a ser el 4

Estructura de la respuesta:
1. Nombre de la receta:
2. Alimentos utilizados:
3. Ingredientes básicos adicionales:
4. Duración:
5. Pasos de preparación:
""".strip()


def modificar_receta_con_llm(receta_generada, alimentos_usados, comentario_usuario):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        raise ErrorGeneracionReceta(
            "No se ha podido modificar la receta porque no está configurada la API del LLM."
        )

    if not receta_generada or not receta_generada.strip():
        raise ErrorGeneracionReceta(
            "No hay una receta previa para modificar."
        )

    if not comentario_usuario or not comentario_usuario.strip():
        raise ErrorGeneracionReceta(
            "Debes escribir una indicación para modificar la receta."
        )

    receta_generada = receta_generada.strip()
    comentario_usuario = comentario_usuario.strip()

    prompt = construir_prompt_feedback_receta(
        receta_generada,
        alimentos_usados,
        comentario_usuario,
    )

    try:
        client = genai.Client(api_key=api_key)

        interaction = client.interactions.create(
            model=model,
            input=prompt,
        )

    except Exception as error:
        error_texto = str(error).lower()

        if (
            "quota" in error_texto
            or "too_many_requests" in error_texto
        ):
            raise ErrorGeneracionReceta(
                "Se ha alcanzado el límite temporal de consultas al LLM. Inténtalo de nuevo más tarde."
            )

        raise ErrorGeneracionReceta(
            "No se ha podido conectar con el servicio de generación de recetas. Inténtalo de nuevo más tarde."
        )

    receta_modificada = interaction.output_text

    if not receta_modificada or not receta_modificada.strip():
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta modificada. Inténtalo de nuevo."
        )

    return receta_modificada