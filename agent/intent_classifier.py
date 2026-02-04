def classify_intent(user_input: str):
    text = user_input.lower()

    if "ticket" in text or "issue" in text or "problem" in text:
        return "CREATE_TICKET"
    elif "what" in text or "how" in text or "explain" in text:
        return "KNOWLEDGE_QUERY"
    else:
        return "GENERAL_CHAT"
