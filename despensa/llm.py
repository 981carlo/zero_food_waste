from google import genai


class ErrorGeneracionReceta(Exception):
    pass


def consultar_llm(api_key, model, prompt, esquema_respuesta):
    try:
        client = genai.Client(api_key=api_key)

        # Solicita al modelo una respuesta JSON ajustada al esquema definido por la aplicación.
        interaction = client.interactions.create(
            model=model,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": esquema_respuesta,
            },
        )

    except Exception as error:
        # Convierte los errores del proveedor en mensajes controlados para la aplicación.
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

    return interaction.output_text