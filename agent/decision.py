def decide_action(user_message: str) -> str:
    """
    Decide what the agent should do
    """

    health_keywords = [
        "fever",
        "blood",
        "diabetes",
        "pressure",
        "headache",
        "hydration",
        "health"
    ]

    message = user_message.lower()

    for keyword in health_keywords:
        if keyword in message:
            return "search_knowledge"

    return "general_reply"

