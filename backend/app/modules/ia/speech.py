"""
Servicio de transcripción de voz.
Recibe audio del browser (webm/ogg) → convierte a WAV → transcribe con SpeechRecognition.
"""
import speech_recognition as sr
import tempfile
import subprocess
import os


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcribe audio bytes to text using Google Speech Recognition."""
    # 1. Save the uploaded audio to a temp file
    suffix = os.path.splitext(filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        tmp_in.write(audio_bytes)
        tmp_in_path = tmp_in.name

    # 2. Convert to WAV using ffmpeg (SpeechRecognition needs WAV)
    tmp_wav = tmp_in_path.replace(suffix, ".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_in_path, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", tmp_wav],
            capture_output=True, timeout=10,
        )
    except Exception as e:
        _cleanup(tmp_in_path, tmp_wav)
        return f"Error convirtiendo audio: {e}"

    if not os.path.exists(tmp_wav):
        _cleanup(tmp_in_path, tmp_wav)
        return "Error: no se pudo convertir el audio."

    # 3. Transcribe with Google Speech Recognition (free, no API key)
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(tmp_wav) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="es-CO")
        return text
    except sr.UnknownValueError:
        return "No pude entender el audio. Intenta de nuevo."
    except sr.RequestError as e:
        return f"Error con el servicio de voz: {e}"
    finally:
        _cleanup(tmp_in_path, tmp_wav)


def _cleanup(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except OSError:
            pass
