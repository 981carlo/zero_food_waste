import os

from dotenv import load_dotenv
from google import genai


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        raise RuntimeError(
            "No se ha configurado GEMINI_API_KEY en el archivo .env"
        )

    client = genai.Client(api_key=api_key)

    interaction = client.interactions.create(
        model=model,
        input=(
            "Responde en español. "
            "Dame una receta sencilla usando arroz, tomate y huevo. "
            "La respuesta debe ser breve."
        ),
    )

    print(interaction.output_text)


if __name__ == "__main__":
    main()