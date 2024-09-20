from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from typing import Union
from dataclasses import dataclass


@dataclass
class Action(JsonPlusSerializer):
    thought: str
    action: str
    action_input: Union[str, dict]
    scratchpad: str
    log: str = None


@dataclass
class Observation(JsonPlusSerializer):
    observation: str
    log: str = None

@dataclass
class ToolOutput(JsonPlusSerializer):
    tool_output: str
    log: str = None

@dataclass
class Finish(JsonPlusSerializer):
    output: str
    log: str = None


@dataclass
class Error(JsonPlusSerializer):
    error: str
    log: str = None
