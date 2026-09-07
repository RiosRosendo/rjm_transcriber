"""
Genera un recap (resumen, decisiones, pendientes) a partir de un transcript,
usando un LLM local via Ollama. Nada sale de tu maquina.

Requiere tener Ollama corriendo (https://ollama.com) y un modelo descargado:
    ollama pull llama3.1

Uso:
    python summarize.py transcripts/junta_20260903_120000.txt
"""
import sys
import os
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"
OUTPUT_DIR = "recaps"

PROMPT_TEMPLATE = """Eres un asistente que resume juntas de trabajo. A continuacion
esta la transcripcion de una reunion (puede tener errores de transcripcion, ignoralos
si no afectan el sentido). Genera un recap en espanol con este formato exacto:

## Resumen general
(2-3 lineas)

## Puntos clave
- bullet points de lo mas importante discutido

## Decisiones tomadas
- lista, o "Ninguna decision explicita" si no hubo

## Pendientes / Action items
- lista con responsable si se menciona, o "No se mencionaron pendientes"

Transcripcion:
{transcript}
"""


def summarize(transcript_path):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    prompt = PROMPT_TEMPLATE.format(transcript=transcript)

    print("Generando recap con el modelo local (Ollama)...")
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=600,
    )
    response.raise_for_status()
    recap = response.json()["response"]

    base_name = os.path.splitext(os.path.basename(transcript_path))[0]
    out_path = os.path.join(OUTPUT_DIR, f"{base_name}_recap.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(recap)

    print(f"\nRecap guardado en: {out_path}\n")
    print(recap)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python summarize.py <ruta_al_transcript.txt>")
        sys.exit(1)
    summarize(sys.argv[1])