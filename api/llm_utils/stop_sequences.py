STOP_SEQUENCES = ["Observation:", "[/WORKSPACE]", "User:", "STOP", "Error:", "AI:"]


def remove_stop_sequences(text: str):
    for seq in STOP_SEQUENCES:
        text = text.replace(seq, "")
    return text
