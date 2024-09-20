import html
import re


HIGHLIGHT = "#FF0073"


def format_message(message: str):
    replaced = (
        message.replace("  ", "....")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("User:", "")
        .replace("Agent:", "")
        .replace("#", "//")
    )

    escaped = html.escape(replaced)
    formatted = re.sub(
        r"(Thought:|Action:|Action Input:|Observation:)", f'<span style="color:{HIGHLIGHT};">\\1</span>', escaped
    )
    return formatted


def create_tool(tool_name: str, tool_input: dict):
    if "python" in tool_name.lower():
        return next(iter(tool_input.values()))
    return {
        "tool_name": tool_name,
        "tool_input": {
            k: v.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r") if isinstance(v, str) else v
            for k, v in tool_input.items()
        },
    }


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
        return "Brain" if "Thought:" in content and "Action:" in content else "Agent"
