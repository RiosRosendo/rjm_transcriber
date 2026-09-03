"""
Captura el audio del sistema (lo que sale por tus bocinas, incluyendo Teams)
usando WASAPI loopback en Windows. No requiere compartir pantalla ni tocar
el cliente de Teams para nada.

Uso:
    python record_audio.py
    (presiona Ctrl+C para detener la grabacion)
"""
import pyaudiowpatch as pyaudio
import wave
import os
import datetime

CHUNK = 1024
OUTPUT_DIR = "recordings"


def get_default_loopback_device(p):
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError(
            "No se encontro un dispositivo loopback para las bocinas por defecto. "
            "Verifica que tengas drivers WASAPI y que no sea un dispositivo Bluetooth raro."
        )
    return default_speakers


def record():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    p = pyaudio.PyAudio()

    device = get_default_loopback_device(p)
    print(f"Grabando audio de: {device['name']}")
    print("Entra a tu junta de Teams normalmente. Presiona Ctrl+C aqui para detener.\n")

    channels = device["maxInputChannels"]
    rate = int(device["defaultSampleRate"])

    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=device["index"],
        frames_per_buffer=CHUNK,
    )

    frames = []
    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        print("\nDeteniendo grabacion...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"junta_{timestamp}.wav")

    wf = wave.open(filepath, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"Guardado en: {filepath}")
    return filepath


if __name__ == "__main__":
    record()