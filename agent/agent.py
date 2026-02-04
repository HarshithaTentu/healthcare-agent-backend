from agent.intent_classifier import classify_intent
from agent.tool_selector import select_tool
from agent.logger import log_decision
from tools.knowledge_tool import knowledge_search
from tools.ticket_tool import create_ticket


def run_agent(user_input: str):
    log_decision("USER_INPUT", user_input)

    intent = classify_intent(user_input)
    log_decision("INTENT_CLASSIFIED", intent)

    tool = select_tool(intent)
    log_decision("TOOL_DECISION", tool)

    if tool == "KNOWLEDGE_SEARCH":
        tool_output = knowledge_search(user_input)
    elif tool == "TICKET_CREATOR":
        tool_output = create_ticket(user_input)
    else:
        tool_output = "No tool required. Responding directly."

    log_decision("TOOL_EXECUTION", tool_output)

    final_response = tool_output
    log_decision("FINAL_RESPONSE", final_response)

    return final_response
