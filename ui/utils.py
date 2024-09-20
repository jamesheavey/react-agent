import html
import re


HIGHLIGHT = "#FF0073"


def format_message(message: str):
    replaced = (
        message.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("User:", "")
        .replace("Agent:", "")
        .replace("#", "//")
        .replace("  ", " ")
    )

    escaped = html.escape(replaced)

    formatted = re.sub(
        r"\[(.*?)\]",
        r"`\1`",
        escaped,
    )
    formatted = re.sub(
        r"`(.*?)`",
        f'<span style="color:{HIGHLIGHT};">`\\1`</span>',
        formatted,
    )

    formatted = re.sub(
        r"(Thought:|Action:|Action Input:|Observation:|Answer:)",
        f'<span style="color:{HIGHLIGHT};">\\1</span>',
        formatted,
    )

    return formatted


def create_tool(tool_name: str, tool_input: dict):
    return tool_input


def get_tool_config(tool_name: str):
    if "python" in tool_name.lower():
        return "Python", "python"
    elif "calc" in tool_name.lower():
        return "Calculator", "json"
    elif "search" in tool_name.lower():
        return "Search", "json"
    else:
        return "Tool", "json"


def get_author(content: str):
    if len(content) < len(" Thought:"):
        if content in " Thought:":
            return "Brain"
        else:
            return "Agent"
    else:
        return "Brain" if "Thought:" in content else "Agent"
