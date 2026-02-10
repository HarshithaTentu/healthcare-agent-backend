import time
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write
import whisper

# -----------------------------
# Load Whisper model once
# -----------------------------
MODEL_NAME = "base"  # tiny | base | small
_model = whisper.load_model(MODEL_NAME)


def listen_and_transcribe(duration_seconds: int = 5) -> str:
    """
    Records audio from microphone and transcribes using Whisper (offline).
    Logs:
    - recording time
    - transcription time
    - total STT time
    """

    total_start = time.perf_counter()
    sample_rate = 16000  # Whisper-friendly sample rate

    print(f"\n🎤 Speak now... (recording {duration_seconds} seconds)")

    # -----------------------------
    # RECORDING TIMING
    # -----------------------------
    record_start = time.perf_counter()
    audio = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    record_ms = (time.perf_counter() - record_start) * 1000

    # -----------------------------
    # SAVE AUDIO
    # -----------------------------
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    write(wav_path, sample_rate, audio)

    print("🧠 Transcribing locally with Whisper...")

    # -----------------------------
    # TRANSCRIPTION TIMING
    # -----------------------------
    transcribe_start = time.perf_counter()
    result = _model.transcribe(wav_path, fp16=False, language="en")
    transcribe_ms = (time.perf_counter() - transcribe_start) * 1000

    text = (result.get("text") or "").strip()
    total_ms = (time.perf_counter() - total_start) * 1000

    # -----------------------------
    # LOG TIMINGS
    # -----------------------------
    print(
        f"⏱️ STT timings | "
        f"recording_ms={record_ms:.2f}, "
        f"transcribe_ms={transcribe_ms:.2f}, "
        f"total_stt_ms={total_ms:.2f}"
    )

    if not text:
        return "Sorry, I couldn't hear that. Please try again."

    print(f"📝 Transcribed text: {text}")
    return text
