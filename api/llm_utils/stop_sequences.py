STOP_SEQUENCES = ["Observation:", "[/WORKSPACE]", "User:", "STOP", "Error:", "AI:"]

FILTER_SEQUENCES = ["[ANSWER_SCHEMA]"]


def remove_stop_sequences(text: str):
    for seq in STOP_SEQUENCES + FILTER_SEQUENCES:
        text = text.replace(seq, "")
    return text
