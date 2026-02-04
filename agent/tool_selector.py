def select_tool(intent: str):
    if intent == "KNOWLEDGE_QUERY":
        return "KNOWLEDGE_SEARCH"
    elif intent == "CREATE_TICKET":
        return "TICKET_CREATOR"
    else:
        return "NO_TOOL"
