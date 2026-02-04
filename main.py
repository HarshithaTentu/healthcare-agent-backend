from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
import json
import logging
import os
from typing import Dict, Tuple

from agent.decision import decide_action
from agent.responder import generate_response

# ----------------------------
# App + logging
# ----------------------------
app = FastAPI(title="Healthcare Information Navigator", version="1.0.0")
logging.basicConfig(level=logging.INFO)


# ----------------------------
# Request models
# ----------------------------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


# ----------------------------
# Knowledge base loader (SAFE)
# ----------------------------
def parse_block(block: str) -> Tuple[str, str] | None:
    """
    Expects block format:
      Question line
      Answer line(s)
    Blocks separated by blank lines.
    Returns (question_lower, answer_text).
    """
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if len(lines) < 2:
        return None
    question = lines[0].lower()
    answer = "\n".join(lines[1:]).strip()
    return question, answer


def load_knowledge() -> Dict[str, str]:
    """
    Loads Q/A from knowledge_base/*.txt safely.
    Returns dict: {question_lower: answer}
    """
    knowledge: Dict[str, str] = {}
    folder = "knowledge_base"

    if not os.path.exists(folder):
        logging.warning(f"Knowledge folder '{folder}' not found. Using empty KB.")
        return knowledge

    for filename in os.listdir(folder):
        if not filename.endswith(".txt"):
            continue

        path = os.path.join(folder, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.warning(f"Could not read {path}: {e}")
            continue

        blocks = content.split("\n\n")
        for block in blocks:
            parsed = parse_block(block)
            if not parsed:
                continue
            q, a = parsed
            # If duplicate questions exist, last one wins (simple rule).
            knowledge[q] = a

    logging.info(f"KB LOADED → {len(knowledge)} entries")
    return knowledge


knowledge_db = load_knowledge()


def find_kb_answer(user_message: str) -> str | None:
    """
    Simple safe match:
    - exact match on full question
    - contains match: question in message OR message in question
    """
    msg = user_message.strip().lower()
    if not msg:
        return None

    # exact match
    if msg in knowledge_db:
        return knowledge_db[msg]

    # contains match
    for q, a in knowledge_db.items():
        if q in msg or msg in q:
            return a

    return None


# ----------------------------
# Basic health check
# ----------------------------
@app.get("/")
def home():
    return {"status": "Backend is running"}


# ----------------------------
# Main text endpoint (your existing agent)
# ----------------------------
@app.post("/agent")
def agent_chat(request: ChatRequest):
    user_message = request.message.strip()

    # Log only small safe details
    logging.info(f"USER INPUT length={len(user_message)}")

    decision = decide_action(user_message)
    logging.info(f"AGENT DECISION → {decision}")

    if decision == "search_knowledge":
        answer = find_kb_answer(user_message)
        if answer:
            return {
                "reply": answer,
                "decision_log": "Agent chose knowledge search → match found",
            }
        return {
            "reply": "I couldn't find exact information in my knowledge base. Please rephrase your question.",
            "decision_log": "Agent chose knowledge search → no match found",
        }

    # No tool → generate response
    try:
        final = generate_response(user_message)
    except Exception as e:
        logging.exception("generate_response failed")
        raise HTTPException(status_code=500, detail="Response generation failed") from e

    return {
        "reply": final,
        "decision_log": "Agent chose NO TOOL → generated response",
    }


# ============================================================
# Day 6 – Twilio Voice (Turn-based Gather) + Status + Stream Mock
# ============================================================

# Twilio import kept safe: if missing, voice endpoints still show error clearly
try:
    from twilio.twiml.voice_response import VoiceResponse, Gather
except Exception:
    VoiceResponse = None
    Gather = None


@app.post("/twilio/voice")
async def twilio_voice_entry():
    """
    Turn-based Twilio voice entry.
    Returns TwiML that gathers speech and posts to /twilio/handle-speech.
    """
    if VoiceResponse is None or Gather is None:
        raise HTTPException(status_code=500, detail="Twilio library not installed. Run: pip install twilio")

    vr = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/twilio/handle-speech",
        method="POST",
        speech_timeout="auto"
    )
    gather.say("Hi! Ask me a healthcare question after the beep.")
    vr.append(gather)

    # If no speech captured, loop again
    vr.say("Sorry, I did not catch that. Please try again.")
    vr.redirect("/twilio/voice", method="POST")

    return Response(str(vr), media_type="text/xml")


@app.post("/twilio/handle-speech")
async def twilio_handle_speech(request: Request):
    """
    Twilio sends recognized speech as a form field: SpeechResult
    We run the same agent logic and respond using TwiML <Say>.
    """
    if VoiceResponse is None:
        raise HTTPException(status_code=500, detail="Twilio library not installed. Run: pip install twilio")

    form = await request.form()
    user_text = (form.get("SpeechResult") or "").strip()

    logging.info(f"TWILIO SPEECH length={len(user_text)}")

    vr = VoiceResponse()

    if not user_text:
        vr.say("I did not hear anything. Please try again.")
        vr.redirect("/twilio/voice", method="POST")
        return Response(str(vr), media_type="text/xml")

    decision = decide_action(user_text)
    logging.info(f"AGENT DECISION (VOICE) → {decision}")

    if decision == "search_knowledge":
        answer = find_kb_answer(user_text)
        if answer:
            vr.say(answer)
        else:
            vr.say("I could not find that in my knowledge base. Please rephrase.")
    else:
        try:
            final = generate_response(user_text)
            vr.say(final)
        except Exception:
            logging.exception("generate_response failed (voice)")
            vr.say("Sorry, something went wrong generating the response. Please try again.")

    vr.redirect("/twilio/voice", method="POST")
    return Response(str(vr), media_type="text/xml")


@app.post("/twilio/status")
async def twilio_status_callback(request: Request):
    """
    Optional status callback endpoint (ringing/in-progress/completed).
    Logs payload safely.
    """
    form = await request.form()
    payload = dict(form)

    # avoid logging full payload (can include phone numbers)
    safe_keys = ["CallStatus", "ApiVersion", "Direction"]
    safe_payload = {k: payload.get(k) for k in safe_keys if k in payload}

    logging.info(f"TWILIO STATUS CALLBACK (safe) → {safe_payload}")
    return JSONResponse({"received": safe_payload})


@app.websocket("/twilio/media")
async def twilio_media_stream(ws: WebSocket):
    """
    Mock WebSocket endpoint for future Twilio Media Streams (audio streaming).
    """
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"ok": False, "error": "Invalid JSON"}))
                continue

            event = data.get("event", "unknown")
            await ws.send_text(json.dumps({"ok": True, "event": event}))
    except WebSocketDisconnect:
        return
