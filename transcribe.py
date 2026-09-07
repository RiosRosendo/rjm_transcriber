"""
Transcribe un archivo de audio usando faster-whisper (100% local).

Para manejar juntas con idiomas mixtos (ej. alguien habla ingles y luego
espanol), el audio se parte en pedazos (chunks) y se detecta el idioma de
CADA pedazo por separado, en vez de asumir un solo idioma para toda la
junta. Esto tarda un poco mas pero es mucho mas confiable cuando hay
cambios de idioma dentro de la misma junta.

Uso:
    python transcribe.py recordings/junta_20260903_120000.wav
"""
import sys
import os
import json
import tempfile
from faster_whisper import WhisperModel
from pydub import AudioSegment

# Opciones de MODEL_SIZE: tiny, base, small, medium, large-v3
# "small" es un buen balance velocidad/calidad en CPU para empezar.
# Si la precision en cambios de idioma no te convence, "medium" ayuda bastante.
MODEL_SIZE = "small"
OUTPUT_DIR = "transcripts"

# Duracion de cada pedazo de audio para detectar idioma por separado.
# Mas chico = detecta cambios de idioma mas rapido, pero tarda mas en total
# y puede cortar frases a la mitad. 20-30s es un buen balance.
CHUNK_LENGTH_MS = 20_000


def split_audio(audio_path, chunk_length_ms=CHUNK_LENGTH_MS):
    """Parte el audio en pedazos de duracion fija. Regresa una lista de
    tuplas (ruta_archivo_temporal, offset_en_segundos)."""
    audio = AudioSegment.from_file(audio_path)
    chunks = []
    tmp_dir = tempfile.mkdtemp(prefix="teams_transcriber_")

    for i, start_ms in enumerate(range(0, len(audio), chunk_length_ms)):
        chunk = audio[start_ms:start_ms + chunk_length_ms]
        chunk_path = os.path.join(tmp_dir, f"chunk_{i:04d}.wav")
        chunk.export(chunk_path, format="wav")
        chunks.append((chunk_path, start_ms / 1000.0))

    return chunks, tmp_dir


def transcribe(audio_path):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Cargando modelo Whisper ({MODEL_SIZE})...")
    # compute_type "int8" corre razonablemente rapido en CPU.
    # Si tienes GPU NVIDIA: device="cuda", compute_type="float16".
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    print("Partiendo el audio en pedazos para detectar idioma por segmento...")
    chunks, tmp_dir = split_audio(audio_path)

    print(f"Transcribiendo {len(chunks)} pedazos (puede tardar varios minutos)...")
    all_segments = []
    last_language = None

    for idx, (chunk_path, offset_seconds) in enumerate(chunks):
        # language=None deja que Whisper detecte el idioma de ESTE pedazo
        # especificamente, en vez de usar un idioma fijo para todo el audio.
        segments, info = model.transcribe(chunk_path, beam_size=5, language=None)
        chunk_language = info.language

        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            entry = {
                "start": round(offset_seconds + seg.start, 2),
                "end": round(offset_seconds + seg.end, 2),
                "text": text,
                "language": chunk_language,
            }
            all_segments.append(entry)

        if chunk_language != last_language:
            print(f"  [{offset_seconds:.0f}s] idioma detectado: {chunk_language}")
            last_language = chunk_language

        os.remove(chunk_path)

    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    last_lang_in_txt = None
    with open(txt_path, "w", encoding="utf-8") as f:
        for entry in all_segments:
            # Marca el idioma en el texto solo cuando cambia, para no saturar
            # el transcript con etiquetas repetidas.
            lang_tag = ""
            if entry["language"] != last_lang_in_txt:
                lang_tag = f"[{entry['language'].upper()}] "
                last_lang_in_txt = entry["language"]
            line = f"[{entry['start']:.1f}s -> {entry['end']:.1f}s] {lang_tag}{entry['text']}"
            print(line)
            f.write(line + "\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_segments, f, ensure_ascii=False, indent=2)

    print(f"\nTranscript guardado en: {txt_path}")
    return txt_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python transcribe.py <ruta_al_wav>")
        sys.exit(1)
    transcribe(sys.argv[1])