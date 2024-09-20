from pydantic import BaseModel


class AgentRequest(BaseModel):
    input: str
    thread_id: str
