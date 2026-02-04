from gtts import gTTS
import os
import time

def speak(text: str):
    filename = f"response_{int(time.time())}.mp3"

    print("🔊 Converting text to speech...")
    tts = gTTS(text=text)
    tts.save(filename)

    print("▶️ Playing audio...")
    os.system(f"afplay {filename}")

    try:
        os.remove(filename)
    except Exception:
        pass
