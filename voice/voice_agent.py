import requests

from voice.stt import listen_and_transcribe
from voice.tts import speak

# Your FastAPI agent endpoint
API_URL = "http://127.0.0.1:8000/agent"


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

    # 1) STT: microphone → text
    user_text = listen_and_transcribe()
    print(f"📝 STT Output: {user_text}")

    # 2) Send text → agent backend
    print("➡️ Calling backend agent...")
    result = call_agent_api(user_text)

    reply = result.get("reply", "")
    decision_log = result.get("decision_log", "")

    print(f"🤖 Agent Reply: {reply}")
    if decision_log:
        print(f"🧾 Decision Log: {decision_log}")

    # 3) TTS: text → audio
    print("🔊 Speaking response...")
    speak(reply)

    print("✅ Done\n")


if __name__ == "__main__":
    run_voice_agent()
