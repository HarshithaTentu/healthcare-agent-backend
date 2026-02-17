import time
import subprocess


def text_to_speech(text: str) -> float:
    """
    Fast offline TTS for macOS using built-in `say`.
    Returns TTS time in ms.
    """
    if not text:
        return 0.0

    start = time.perf_counter()

    # You can tune speed with -r (words/min). 190 is a good natural speed.
    subprocess.run(["say", "-r", "190", text], check=False)

    return (time.perf_counter() - start) * 1000
