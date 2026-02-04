import time
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write
import whisper


# Load Whisper model once (faster on next runs)
# Options: "tiny" (fastest), "base" (good balance), "small" (better accuracy, slower)
MODEL_NAME = "base"
_model = whisper.load_model(MODEL_NAME)


def listen_and_transcribe(duration_seconds: int = 5) -> str:
    """
    Records audio from microphone for duration_seconds and transcribes using Whisper offline.
    """
    sample_rate = 16000  # Whisper friendly sample rate

    print(f"\n🎤 Speak now... (recording {duration_seconds} seconds)")
    audio = sd.rec(int(duration_seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    print("🧠 Transcribing locally with Whisper...")

    # Save to a temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    write(wav_path, sample_rate, audio)

    # Whisper transcription
    result = _model.transcribe(wav_path, fp16=False, language="en")  # fp16=False for compatibility
    text = (result.get("text") or "").strip()

    if not text:
        return "Sorry, I couldn't hear that. Please try again."
    print(f"📝 Transcribed text: {text}")
    return text
