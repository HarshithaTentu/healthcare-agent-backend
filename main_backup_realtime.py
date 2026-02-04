from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
import json
import logging
import os

from agent.decision import decide_action
from agent.responder import generate_response

app = FastAPI(title="Healthcare Information Navigator")
logging.basicConfig(level=logging.INFO)


class ChatRequest(BaseModel):
    message: str


def load_knowledge():
    """
    Loads knowledge from /knowledge_base/*.txt
    Format expected in txt:
    Question line
    Answer line(s)

    (Blocks separated by blank lines)
    """
    knowledge = {}
    folder = "knowledge_base"

    # ✅ prevent crash if folder missing
    if not os.path.exists(folder):
        logging.warning(f"Knowledge folder '{folder}' not found. Using empty KB.")
        return knowledge

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as file:
                blocks = file.read().split("\n\n")
                for block in blocks:
                    lines = [l.strip() for l in block.split("\n") if l.strip()]
                    if not lines:
                        continue

                    question = lines[0].lower()
                    knowledge[question] = block

    logging.info(f"KB LOADED → {len(knowledge)} entries")
    return knowledge


knowledge_db = load_knowledge()


@app.get("/")
def home():
    return {"status": "Backend is running"}


@app.post("/agent")
def agent_chat(request: ChatRequest):
    user_message = request.message.strip()

    # ✅ STEP 1: log input
    logging.info(f"USER INPUT → {user_message}")

    # ✅ STEP 2: decide tool/action
    decision = decide_action(user_message)
    logging.info(f"AGENT DECISION → {decision}")

    # ✅ STEP 3: execute tool
    if decision == "search_knowledge":
        logging.info("TOOL SELECTED → knowledge_search")

        msg = user_message.lower()
        for question, answer in knowledge_db.items():
            # ✅ better matching
            if question in msg or msg in question:
                logging.info("TOOL RESULT → KB match found")
                logging.info("FINAL RESPONSE → returned KB answer")

                return {
                    "reply": answer,
                    "decision_log": f"User asked '{user_message}' → Agent chose KB tool → Match found"
                }

        logging.info("TOOL RESULT → No KB match found")
        logging.info("FINAL RESPONSE → asked user to rephrase")

        return {
            "reply": "I couldn't find exact information in my knowledge base. Please rephrase your question.",
            "decision_log": f"User asked '{user_message}' → Agent chose KB tool → No match found"
        }

    # ✅ STEP 4: compose final response (no tool)
    logging.info("TOOL SELECTED → none")
    logging.info("RESPONSE METHOD → generate_response")

    final = generate_response(user_message)

    logging.info("FINAL RESPONSE → generated response returned")

    return {
        "reply": final,
        "decision_log": f"User asked '{user_message}' → Agent chose NO TOOL → Generated response"
    }


# ============================================================
# Day 6 – Telephony Mock (Twilio-like Webhooks + Media Stream)
# ============================================================

def twiml(xml_body: str) -> Response:
    """Return TwiML (XML) with correct content-type for Twilio."""
    return Response(content=xml_body.strip(), media_type="text/xml")


@app.post("/twilio/voice")
async def twilio_incoming_call(request: Request):
    """
    Mock Twilio Voice webhook.
    Twilio would POST here when a call arrives.
    We respond with TwiML (XML) instructions.
    """
    form = await request.form()

    call_sid = form.get("CallSid", "SIMULATED_CALL_SID")
    from_number = form.get("From", "SIMULATED_FROM")
    to_number = form.get("To", "SIMULATED_TO")

    response_xml = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice">
            Hello! This is a simulated Twilio webhook.
            CallSid: {call_sid}.
            From {from_number} to {to_number}.
        </Say>
        <Hangup/>
    </Response>
    """
    return twiml(response_xml)


@app.post("/twilio/status")
async def twilio_status_callback(request: Request):
    """
    Mock status callback endpoint.
    In real Twilio, this receives events like ringing/in-progress/completed.
    """
    form = await request.form()
    payload = dict(form)
    return JSONResponse({"received": payload})


@app.websocket("/twilio/media")
async def twilio_media_stream(ws: WebSocket):
    """
    Mock Twilio Media Streams receiver.
    In real Twilio Media Streams, Twilio connects via WebSocket and sends JSON:
      { "event": "start" }
      { "event": "media", "media": { "payload": "<base64 audio>" } }
      { "event": "stop" }
    Here we just read JSON and echo back acknowledgement.
    """
    await ws.accept()
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            event = data.get("event", "unknown")

            # In real life:
            # - if event == "media": decode audio payload and send to STT
            # - then LLM -> TTS -> respond back (advanced)
            await ws.send_text(json.dumps({"ok": True, "event": event}))
    except WebSocketDisconnect:
        return
