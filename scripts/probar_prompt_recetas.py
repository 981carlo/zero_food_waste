import os
from datetime import date, timedelta

from dotenv import load_dotenv
from google import genai


def construir_prompt(alimentos):
    hoy = date.today()
    limite_proximos = hoy + timedelta(days=7)

    lineas_alimentos = []

    for alimento in alimentos:
        fecha_caducidad = alimento["fecha_caducidad"]

        if hoy <= fecha_caducidad <= limite_proximos:
            prioridad = "prioritario por caducidad próxima"
        else:
            prioridad = "no prioritario"

        lineas_alimentos.append(
            f"- {alimento['nombre']}: "
            f"{alimento['cantidad']} {alimento['unidad_medida']}, "
            f"caduca el {fecha_caducidad.isoformat()} "
            f"({prioridad})"
        )

    alimentos_texto = "\n".join(lineas_alimentos)

    return f"""
Eres un asistente culinario para una aplicación web orientada a reducir el desperdicio alimentario doméstico.

Tu tarea es proponer una receta sencilla a partir de los alimentos disponibles del usuario.

Fecha actual: {hoy.isoformat()}

Alimentos disponibles:
{alimentos_texto}

Instrucciones:
- Responde siempre en español.
- Prioriza los alimentos marcados como prioritarios por caducidad próxima.
- Propón una receta realista y sencilla.
- No inventes ingredientes principales que no estén en la lista.
- Puedes asumir ingredientes básicos de cocina como sal, aceite, agua o especias.
- La respuesta debe ser clara y fácil de mostrar en una página web.

Estructura de la respuesta:
1. Nombre de la receta
2. Alimentos utilizados
3. Ingredientes básicos adicionales, si hacen falta
4. Duración
5. Pasos de preparación
""".strip()


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        raise RuntimeError(
            "No se ha configurado GEMINI_API_KEY en el archivo .env"
        )

    alimentos = [
        {
            "nombre": "Tallarines",
            "cantidad": "500",
            "unidad_medida": "gramos",
            "fecha_caducidad": date.today() + timedelta(days=2),
        },
        {
            "nombre": "Tomate",
            "cantidad": "3",
            "unidad_medida": "unidades",
            "fecha_caducidad": date.today() + timedelta(days=4),
        },
        {
            "nombre": "Leche",
            "cantidad": "1",
            "unidad_medida": "litros",
            "fecha_caducidad": date.today() + timedelta(days=20),
        },
    ]

    prompt = construir_prompt(alimentos)

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=prompt,
    )

    print(interaction.output_text)


if __name__ == "__main__":
    main()