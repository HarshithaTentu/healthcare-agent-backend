import time
from gtts import gTTS


def speak(text: str, filename: str = "response.mp3") -> str:
    """
    Converts text to speech and logs TTS time.
    """
    start = time.perf_counter()

    tts = gTTS(text=text)
    tts.save(filename)

    tts_ms = (time.perf_counter() - start) * 1000
    print(f"⏱️ TTS timing | tts_ms={tts_ms:.2f}, text_len={len(text)}")

    return filename
