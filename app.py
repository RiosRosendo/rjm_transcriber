"""
App de escritorio: ventana simple con pywebview que envuelve el pipeline
de grabacion + transcripcion + resumen. Ejecutar con: python app.py
"""
import webview
import traceback

from recorder import Recorder
from transcribe import transcribe
from summarize import summarize

recorder = Recorder()


class Api:
    def start_recording(self):
        try:
            recorder.start()
            return {"status": "recording"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def stop_recording_and_process(self):
        try:
            wav_path = recorder.stop()
            if not wav_path:
                return {"status": "error", "message": "No se estaba grabando o no se capturo audio."}

            txt_path = transcribe(wav_path)
            recap_path = summarize(txt_path)

            with open(recap_path, "r", encoding="utf-8") as f:
                recap_text = f.read()

            return {"status": "done", "recap": recap_text, "recap_path": recap_path}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    api = Api()
    window = webview.create_window(
        "Asistente de Juntas",
        "ui/index.html",
        js_api=api,
        width=480,
        height=650,
        resizable=True,
    )
    webview.start()