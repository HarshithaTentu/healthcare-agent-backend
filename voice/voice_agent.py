import time
import requests
from datetime import datetime

from voice.stt import listen_and_transcribe
from voice.tts import speak

# Your FastAPI agent endpoint
API_URL = "http://127.0.0.1:8000/agent"

# Log file path (make sure logs/ folder exists)
LOG_FILE = "logs/latency.log"


def append_log(line: str) -> None:
    """Append one line to logs/latency.log"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def call_agent_api(user_text: str) -> dict:
    """
    Sends text to the backend agent API and returns JSON response.
    Backend expects: { "message": "..." }
    Backend returns: { "reply": "...", "decision_log": "..." }
    """
    payload = {"message": user_text}

    try:
        res = requests.post(API_URL, json=payload, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        return {
            "reply": f"Sorry, I could not reach the agent server. Error: {e}",
            "decision_log": "Voice client → backend API call failed"
        }


def run_voice_agent():
    print("\n🎧 Voice Agent Started (API mode)")
    print(f"🌐 Backend: {API_URL}")

    run_ts = datetime.now().isoformat(timespec="seconds")

    total_start = time.perf_counter()

    # 1) STT: microphone → text
    stt_start = time.perf_counter()
    user_text = listen_and_transcribe()
    stt_ms = (time.perf_counter() - stt_start) * 1000
    print(f"📝 STT Output: {user_text}")
    print(f"⏱️ STT time: {stt_ms:.2f} ms")

    # 2) Send text → agent backend (API timing)
    print("➡️ Calling backend agent...")
    api_start = time.perf_counter()
    result = call_agent_api(user_text)
    api_ms = (time.perf_counter() - api_start) * 1000

    reply = result.get("reply", "")
    decision_log = result.get("decision_log", "")

    print(f"🤖 Agent Reply: {reply}")
    if decision_log:
        print(f"🧾 Decision Log: {decision_log}")
    print(f"⏱️ API time: {api_ms:.2f} ms")

    # 3) TTS: text → audio
    print("🔊 Speaking response...")
    tts_start = time.perf_counter()
    speak(reply)
    tts_ms = (time.perf_counter() - tts_start) * 1000
    print(f"⏱️ TTS time: {tts_ms:.2f} ms")

    total_ms = (time.perf_counter() - total_start) * 1000
    print("✅ Done")
    print(f"⏱️ TOTAL voice pipeline time: {total_ms:.2f} ms\n")

    # 4) Save one clean log line (easy to analyze later)
    # Example:
    # ts=2026-02-10T18:00:00 stt_ms=... api_ms=... tts_ms=... total_ms=... stt_text_len=... reply_len=...
    append_log(
        f"ts={run_ts} stt_ms={stt_ms:.2f} api_ms={api_ms:.2f} tts_ms={tts_ms:.2f} total_ms={total_ms:.2f} "
        f"stt_text_len={len(user_text)} reply_len={len(reply)}"
    )


if __name__ == "__main__":
    run_voice_agent()
