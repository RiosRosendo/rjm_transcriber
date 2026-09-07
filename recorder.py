"""
Grabador de audio del sistema, controlado por start()/stop() en vez de
Ctrl+C, para poder llamarlo desde botones de una interfaz grafica.
"""
import pyaudiowpatch as pyaudio
import wave
import os
import datetime
import threading

CHUNK = 1024
OUTPUT_DIR = "recordings"
SAMPLE_WIDTH_INT16 = 2  # bytes, fijo para pyaudio.paInt16


def get_default_loopback_device(p):
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers.get("isLoopbackDevice", False):
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError(
            "No se encontro un dispositivo loopback para las bocinas por defecto."
        )
    return default_speakers


class Recorder:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._frames = []
        self._channels = None
        self._rate = None
        self.is_recording = False

    def start(self):
        if self.is_recording:
            return
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._stop_event.clear()
        self._frames = []
        self.is_recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def _record_loop(self):
        p = pyaudio.PyAudio()
        try:
            device = get_default_loopback_device(p)
            self._channels = device["maxInputChannels"]
            self._rate = int(device["defaultSampleRate"])

            stream = p.open(
                format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._rate,
                input=True,
                input_device_index=device["index"],
                frames_per_buffer=CHUNK,
            )

            while not self._stop_event.is_set():
                data = stream.read(CHUNK, exception_on_overflow=False)
                self._frames.append(data)

            stream.stop_stream()
            stream.close()
        finally:
            p.terminate()

    def stop(self):
        """Detiene la grabacion, guarda el WAV y regresa la ruta del archivo."""
        if not self.is_recording:
            return None
        self._stop_event.set()
        self._thread.join()
        self.is_recording = False

        if not self._frames:
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(OUTPUT_DIR, f"junta_{timestamp}.wav")

        wf = wave.open(filepath, "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(SAMPLE_WIDTH_INT16)
        wf.setframerate(self._rate)
        wf.writeframes(b"".join(self._frames))
        wf.close()

        return filepath