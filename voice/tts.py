import time
import subprocess
from gtts import gTTS


def speak(text: str, filename: str = "response.mp3") -> str:
    """
    Converts text to speech using gTTS, saves mp3, and plays it (macOS).
    """
    start = time.perf_counter()

    tts = gTTS(text=text)
    tts.save(filename)

    tts_ms = (time.perf_counter() - start) * 1000
    print(f"⏱️ TTS timing | tts_ms={tts_ms:.2f}, text_len={len(text)}, file={filename}")

    # macOS playback
    try:
        subprocess.run(["afplay", filename], check=True)
    except Exception as e:
        print(f"⚠️ Could not play audio automatically. Error: {e}")
        print(f"✅ File saved as: {filename} (try double-clicking it)")

    return filename
