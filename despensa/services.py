import os
import json

from decimal import Decimal, InvalidOperation

from datetime import timedelta

from django.utils import timezone

from .llm import consultar_llm, ErrorGeneracionReceta

def formatear_cantidad(cantidad):
    if cantidad == cantidad.to_integral():
        return str(int(cantidad))

    return str(cantidad).replace(".", ",")

def construir_esquema_respuesta(alimentos):
    """
    Construye el esquema JSON que debe devolver el LLM,
    incluyendo los códigos válidos de los alimentos disponibles.
    """
    codigos_alimentos = [
        f"A{indice}"
        for indice, _ in enumerate(alimentos, start=1)
    ]

    return {
        "type": "object",
        "properties": {
            "receta": {
                "type": "string",
            },
            "alimentos_utilizados": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "codigo": {
                            "type": "string",
                            "enum": codigos_alimentos,
                        },
                        "cantidad_utilizada": {
                            "type": "number",
                        },
                    },
                    "required": [
                        "codigo",
                        "cantidad_utilizada",
                    ],
                },
            },
        },
        "required": [
            "receta",
            "alimentos_utilizados",
        ],
    }

def procesar_respuesta_llm(respuesta, alimentos):
    """
    Procesa la respuesta JSON del LLM y relaciona los códigos
    de los alimentos utilizados con los registros de la despensa.
    """
    try:
        datos_respuesta = json.loads(respuesta)
    except (json.JSONDecodeError, TypeError):
        raise ErrorGeneracionReceta(
            "El LLM ha devuelto una respuesta con un formato no válido. Inténtalo de nuevo."
        )

    receta = datos_respuesta.get("receta", "").strip()
    alimentos_utilizados = datos_respuesta.get("alimentos_utilizados", [])

    # Relaciona los códigos enviados al LLM con los alimentos originales.
    mapa_alimentos = {
        f"A{indice}": alimento
        for indice, alimento in enumerate(alimentos, start=1)
    }
    
    for codigo in mapa_alimentos:
        receta = receta.replace(f" ({codigo})", "")

    alimentos_procesados = []

    for alimento_utilizado in alimentos_utilizados:
        codigo = alimento_utilizado.get("codigo")
        cantidad_utilizada = alimento_utilizado.get("cantidad_utilizada")

        alimento = mapa_alimentos.get(codigo)

        if alimento is None:
            continue
        
        try:
            if isinstance(cantidad_utilizada, bool):
                raise ValueError

            cantidad_decimal = Decimal(str(cantidad_utilizada))
        except (InvalidOperation, ValueError, TypeError):
            raise ErrorGeneracionReceta(
                "El LLM ha devuelto una cantidad no válida. Inténtalo de nuevo."
            )

        if not cantidad_decimal.is_finite() or cantidad_decimal <= 0:
            raise ErrorGeneracionReceta(
                "El LLM ha devuelto una cantidad no válida. Inténtalo de nuevo."
            )

        if cantidad_decimal > alimento.cantidad:
            raise ErrorGeneracionReceta(
                f"El LLM ha indicado una cantidad de {alimento.nombre} "
                "superior a la disponible. Inténtalo de nuevo."
            )

        alimentos_procesados.append({
            "id": str(alimento.id),
            "nombre": alimento.nombre,
            "cantidad_utilizada": cantidad_utilizada,
            "unidad_medida": alimento.unidad_medida,
        })

    return receta, alimentos_procesados


def construir_prompt_recetas(alimentos, usar_todos_los_alimentos=False, indicaciones_usuario="" ):
    """Construye el prompt para generar una receta a partir de los alimentos disponibles."""
    hoy = timezone.localdate()
    limite_proximos = hoy + timedelta(days=7)

    lineas_alimentos = []

    # Asigna un código a cada alimento e indica si debe priorizarse por caducidad.
    for indice, alimento in enumerate(alimentos, start=1):
        fecha_caducidad = alimento.fecha_caducidad
        codigo = f"A{indice}"

        if hoy <= fecha_caducidad <= limite_proximos:
            prioridad = "prioritario por caducidad próxima"
        else:
            prioridad = "no prioritario"

        lineas_alimentos.append(
            f"- {codigo} | {alimento.nombre}: "
            f"{formatear_cantidad(alimento.cantidad)} {alimento.unidad_medida}, "
            f"caduca el {fecha_caducidad.isoformat()} "
            f"({prioridad})"
        )

    lista_alimentos = "\n".join(lineas_alimentos)

    # Adapta el prompt según se use toda la despensa o una selección del usuario.
    if usar_todos_los_alimentos:
        instruccion_uso_alimentos = (
            "Debes utilizar todos los alimentos de la lista, porque han sido seleccionados por el usuario."
        )
    else:
        instruccion_uso_alimentos = (
            "No es necesario utilizar todos los alimentos de la lista; selecciona solo los que encajen bien en una receta coherente."
        )

    indicaciones_usuario = indicaciones_usuario.strip()

    if indicaciones_usuario:
        indicaciones = (
            "\nIndicaciones adicionales del usuario:\n"
            f"{indicaciones_usuario}"
        )
    else:
        indicaciones = ""

    return f"""
Eres un asistente culinario para una aplicación web orientada a reducir el desperdicio alimentario doméstico.

Tu tarea es proponer una receta sencilla a partir de los alimentos disponibles del usuario.

Fecha actual: {hoy.isoformat()}

Alimentos disponibles:
{lista_alimentos}
{indicaciones}

Instrucciones:
- Responde siempre en español.
- Prioriza los alimentos marcados como prioritarios por caducidad próxima.
- {instruccion_uso_alimentos}
- Respeta las indicaciones adicionales del usuario cuando se hayan proporcionado.
- Propón una receta realista y sencilla.
- No inventes ingredientes principales que no estén en la lista.
- Puedes asumir ingredientes básicos de cocina como sal, aceite, agua o especias.
- Usa medidas lógicas, no pongas cosas como "7,25 gramos de sal". Pon la medida en redondeada y su equivalencia cuando proceda. Por ejemplo: "225 ml de leche o una taza"
- No uses formato Markdown.
- No uses almohadillas, asteriscos ni separadores con guiones.
- Usa texto plano, claro y fácil de mostrar en una página web.
- Si no se utilizan ingredientes básicos adicionales, no incluyas ese apartado en la receta.
- Si detectas algo en la lista de alimentos que no sea un alimento, no lo incluyas en la receta. De ser así, añade un nuevo punto en la respuesta indicando qué elemento ha sido descartado por no ser un alimento
- Para cada alimento de la lista que utilices realmente en la receta, incluye su código en alimentos_utilizados.
- La cantidad_utilizada debe expresarse en la misma unidad de medida en la que aparece ese alimento en la lista y nunca puede superar la cantidad disponible.
- Si muestras una unidad diferente en el texto de la receta, convierte cantidad_utilizada a la unidad de la despensa.
- Por ejemplo: si la leche está registrada en litros y utilizas 250 ml, devuelve cantidad_utilizada: 0.25, nunca 250.
- Si un alimento está registrado en kilogramos y utilizas 200 gramos, devuelve cantidad_utilizada: 0.2, nunca 200.
- No incluyas en alimentos_utilizados ingredientes básicos adicionales como sal, agua, aceite o especias, salvo que formen parte de la despensa identificada con un código.
- No muestres los códigos A1, A2, A3, etc. en el texto de la receta; utilízalos únicamente para identificar los alimentos en alimentos_utilizados.
- Respeta estrictamente la estructura indicada y utiliza saltos de línea reales entre cada apartado.
- En "Alimentos utilizados", muestra cada alimento en una línea independiente.
- En "Ingredientes básicos adicionales", muestra cada ingrediente en una línea independiente.
- En "Pasos de preparación", escribe cada paso numerado en una línea independiente.
- Nunca escribas varios pasos de preparación en la misma línea.

El texto de la receta debe seguir exactamente esta estructura:

Nombre de la receta: [nombre]

Alimentos utilizados:
- [alimento]: [cantidad y unidad]
- [alimento]: [cantidad y unidad]

Ingredientes básicos adicionales:
- [ingrediente]
- [ingrediente]

Duración: [duración]

Pasos de preparación:
1. [primer paso]
2. [segundo paso]
3. [tercer paso]

""".strip()


def generar_receta_con_llm(alimentos, usar_todos_los_alimentos=False, indicaciones_usuario=""):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        raise ErrorGeneracionReceta(
            "No se ha podido generar la receta porque no está configurada la API del LLM."
        )

    prompt = construir_prompt_recetas(
        alimentos,
        usar_todos_los_alimentos=usar_todos_los_alimentos,
        indicaciones_usuario=indicaciones_usuario,
    )

    # Define el formato estructurado que debe devolver el LLM.
    esquema_respuesta = construir_esquema_respuesta(alimentos)

    respuesta = consultar_llm(
        api_key,
        model,
        prompt,
        esquema_respuesta,
    )

    if not respuesta or not respuesta.strip():
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta. Inténtalo de nuevo."
        )

    receta, alimentos_utilizados = procesar_respuesta_llm(
        respuesta,
        alimentos,
    )

    if not receta:
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta. Inténtalo de nuevo."
        )

    return {
        "receta": receta,
        "alimentos_utilizados": alimentos_utilizados,
    }

def construir_prompt_feedback_receta(receta_generada, alimentos_disponibles, comentario_usuario):
    # Asigna códigos a los alimentos usados para identificarlos en la respuesta estructurada.
    alimentos_usados_texto = "\n".join(
        f"- A{indice} | {alimento.nombre}: "
        f"{formatear_cantidad(alimento.cantidad)} {alimento.unidad_medida}"
        for indice, alimento in enumerate(alimentos_disponibles, start=1)
    )
    return f"""
Eres un asistente culinario para una aplicación web orientada a reducir el desperdicio alimentario doméstico.

El usuario ya ha recibido esta receta:

{receta_generada}

Estos son los alimentos principales permitidos para la receta modificada:

{alimentos_usados_texto}

Ahora el usuario quiere modificarla con esta indicación:

{comentario_usuario}

Tu tarea es generar una nueva versión de la receta teniendo en cuenta la indicación del usuario.

Instrucciones:
- Responde siempre en español.
- Mantén una receta realista y sencilla.
- Respeta la intención del usuario.
- Utiliza como alimentos principales únicamente alimentos presentes en la lista anterior.
- Puedes incorporar alimentos de esa lista aunque no aparecieran en la receta original, si son necesarios para cumplir la nueva indicación del usuario.
- No inventes ni añadas alimentos principales que no aparezcan en la lista anterior.
- Si la indicación del usuario no puede cumplirse con los alimentos disponibles, no inventes ingredientes para intentar cumplirla.
- Solo puedes añadir ingredientes básicos habituales como agua, sal, aceite, especias o condimentos.
- No uses formato Markdown.
- No uses almohadillas, asteriscos ni separadores con guiones.
- Usa texto plano, claro y fácil de mostrar en una página web.
- Si no se utilizan ingredientes básicos adicionales, no incluyas ese apartado en la receta.
- Para cada alimento de la lista que utilices realmente en la receta modificada, incluye su código en alimentos_utilizados.
- La cantidad_utilizada debe expresarse en la misma unidad de medida en la que aparece ese alimento en la lista y nunca puede superar la cantidad disponible.
- Si muestras una unidad diferente en el texto de la receta, convierte cantidad_utilizada a la unidad de la despensa.
- Por ejemplo: si la leche está registrada en litros y utilizas 250 ml, devuelve cantidad_utilizada: 0.25, nunca 250.
- Si un alimento está registrado en kilogramos y utilizas 200 gramos, devuelve cantidad_utilizada: 0.2, nunca 200.
- No incluyas en alimentos_utilizados ingredientes básicos adicionales como sal, agua, aceite o especias, salvo que formen parte de la despensa identificada con un código.
- No muestres los códigos A1, A2, A3, etc. en el texto de la receta; utilízalos únicamente para identificar los alimentos en alimentos_utilizados.
- Respeta estrictamente la estructura indicada y utiliza saltos de línea reales entre cada apartado.
- En "Alimentos utilizados", muestra cada alimento en una línea independiente.
- En "Ingredientes básicos adicionales", muestra cada ingrediente en una línea independiente.
- En "Pasos de preparación", escribe cada paso numerado en una línea independiente.
- Nunca escribas varios pasos de preparación en la misma línea.

El texto de la receta debe seguir exactamente esta estructura:

Nombre de la receta: [nombre]

Alimentos utilizados:
- [alimento]: [cantidad y unidad]
- [alimento]: [cantidad y unidad]

Ingredientes básicos adicionales:
- [ingrediente]
- [ingrediente]

Duración: [duración]

Pasos de preparación:
1. [primer paso]
2. [segundo paso]
3. [tercer paso]

""".strip()


def modificar_receta_con_llm(receta_generada, alimentos_disponibles, comentario_usuario):
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

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

    if not api_key:
        raise ErrorGeneracionReceta(
            "No se ha podido modificar la receta porque no está configurada la API del LLM."
        )

    prompt = construir_prompt_feedback_receta(
        receta_generada,
        alimentos_disponibles,
        comentario_usuario,
    )

    # Incluye en la respuesta estructurada únicamente los alimentos usados en la receta anterior.
    esquema_respuesta = construir_esquema_respuesta(alimentos_disponibles)

    respuesta = consultar_llm(
        api_key,
        model,
        prompt,
        esquema_respuesta,
    )

    if not respuesta or not respuesta.strip():
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta modificada. Inténtalo de nuevo."
        )

    receta_modificada, alimentos_utilizados = procesar_respuesta_llm(
        respuesta,
        alimentos_disponibles,
    )

    if not receta_modificada:
        raise ErrorGeneracionReceta(
            "El LLM no ha devuelto ninguna receta modificada. Inténtalo de nuevo."
        )

    return {
        "receta": receta_modificada,
        "alimentos_utilizados": alimentos_utilizados,
    }