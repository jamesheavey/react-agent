import re
from typing import Union
from schema.agent_outputs import Action, Finish, Error, Observation
from langchain_core.messages import AIMessage
from tools.tools import get_tools
from llm_utils.stop_sequences import remove_stop_sequences
import json
from graph.utils import send_event


def plan_parser(ai_message: AIMessage) -> list[str]:
    return ai_message.content.strip()


def react_parser(ai_message: AIMessage) -> Union[Action, Finish, Error]:
    log = ai_message.content
    text = remove_stop_sequences(log)

    tool_names = get_tools().names

    react_regex = (
        r"(?:Thought\s*:\s*(.*?)\s*)?Action\s*:\s*(.*?)\s*Action\s*Input\s*:\s*(.*?)(?:\s*Observation\s*:.*)?$"
    )
    react_match = re.search(react_regex, text, re.DOTALL)
    if react_match:
        try:
            thought = react_match.group(1).strip() if react_match.group(1) else ""

            action = react_match.group(2).strip()
            if action not in tool_names:
                error = f"Invalid Action `{action}`, must be one of {tool_names}"
                send_event("error", error)
                return Error(log=text, error=error)

            action_input = json.loads(react_match.group(3).strip())

            if not thought and text.startswith("Action"):
                thought = ""
            elif not thought:
                thought = text.split("Action")[0].strip()
            return Action(
                thought=thought,
                action=action,
                action_input=action_input,
                log=log,
                scratchpad=text.strip(),
            )
        except Exception as e:
            error = f"Invalid Action Input for `{action}`, retry the action but resolve the error: < {str(e)} >"
            send_event("error", error)
            return Error(
                log=text,
                error=error,
            )

    return Finish(
        output=text.replace("Agent:", "").strip(),
        log=log,
    )

    # finish_regex = r"(?:Thought\s*:\s*(.*?)\s*)?Answer\s*:\s*(.*?)\s*$"
    # finish_match = re.search(finish_regex, text, re.DOTALL)
    # if finish_match:
    #     thought = finish_match.group(1).strip() if finish_match.group(1) else ""
    #     answer = finish_match.group(2).strip()
    #     return Finish(
    #         thought=thought,
    #         output=answer,
    #         log=log,
    #     )

    # error = f"Could not find a matching [TOOL_CALL_SCHEMA] or [ANSWER_SCHEMA] pattern in the output, please try again."
    # send_event("error", error)
    # return Error(
    #     log=log,
    #     error=error,
    # )


def observation_parser(ai_message: AIMessage) -> Observation:
    text = ai_message.content
    observation_regex = r"Observation\s*:\s*(.*)$"
    observation_match = re.search(observation_regex, text, re.DOTALL)
    if observation_match:
        observation = observation_match.group(1).strip()
        return Observation(observation=observation)
    else:
        return Observation(observation=text.strip())
