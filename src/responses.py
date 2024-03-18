import random


def handle_response(message) -> str:
    p_message = message.lower()

    if p_message == "hello":
        return "Hi!"

    if p_message == "roll":
        return str(random.randint(1, 6))

    if p_message == "help":
        return "Commands: !roll, !hello, !help, !refresh(only in verification channel)"
