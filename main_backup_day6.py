from fastapi import FastAPI
from pydantic import BaseModel
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
