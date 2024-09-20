from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from dataclasses import dataclass
from typing import Literal


@dataclass
class Message(JsonPlusSerializer):
    role: Literal["User", "Agent"]
    content: str
