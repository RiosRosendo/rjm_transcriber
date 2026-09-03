"""
Transcribe un archivo de audio usando faster-whisper (100% local, sin
mandar audio a ningun servidor).

Uso:
    python transcribe.py recordings/junta_20260903_120000.wav
"""
import sys
import os
import json
from faster_whisper import WhisperModel

# Opciones de MODEL_SIZE: tiny, base, small, medium, large-v3
# "small" es un buen balance velocidad/calidad en CPU para empezar. puede ser mayor el modelo pero es aun mas carga de CPU 
MODEL_SIZE = "small"
OUTPUT_DIR = "transcripts"


def transcribe(audio_path):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Cargando modelo Whisper ({MODEL_SIZE})...")
    # compute_type "int8" corre razonablemente rapido en CPU.
    # Si tienes GPU NVIDIA con CUDA: device="cuda", compute_type="float16".
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    print("Transcribiendo (puede tardar varios minutos segun la duracion)...")
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"Idioma detectado: {info.language} (prob {info.language_probability:.2f})")

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    all_segments = []
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            line = f"[{seg.start:.1f}s -> {seg.end:.1f}s] {seg.text.strip()}"
            print(line)
            f.write(line + "\n")
            all_segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_segments, f, ensure_ascii=False, indent=2)

    print(f"\nTranscript guardado en: {txt_path}")
    return txt_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python transcribe.py <ruta_al_wav>")
        sys.exit(1)
    transcribe(sys.argv[1])