import logging, os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langchain_core.runnables import Runnable
from llm_utils.stop_sequences import STOP_SEQUENCES, remove_stop_sequences
from schema.api_schema import AgentRequest
from graph.graph_builder import GraphBuilder
from tools.tools import get_tools
from fastapi.responses import StreamingResponse
import json
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.ERROR, format="%(message)s")

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    llm = None

    if os.getenv("ANTHROPIC_API_KEY", None):
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

    elif os.getenv("OPENAI_API_KEY", None):
        llm = ChatOpenAI(model="gpt-4o")

    if not llm:
        raise Exception("No API keys specified")

    app.state.agent = GraphBuilder(llm=llm, verbose=True).build_graph()

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_agent():
    return app.state.agent


@app.get("/")
async def root():
    return {
        "message": "ReAct Agent - Custom LangGraph LLM Agent API",
        "version": "1.0.0",
        "description": "This API enables you to query a custom ReAct LLM agent with natural language.",
        "endpoints": {
            "/docs": "View the interactive API documentation",
            "/agent": "Query the agent with natural language",
            "/stream_agent": "Stream response from the agent with natural language query",
        },
        "github": "https://github.ibm.com/TechnologyGarageUKI/watsonx-agent",
    }


@app.post("/agent")
async def agent(body: AgentRequest, agent: Runnable = Depends(get_agent)):
    config = {"configurable": {"thread_id": body.thread_id}}
    return agent.invoke(
        {
            "input": body.input,
        },
        config,
    )


@app.post("/stream_agent")
async def stream_agent(body: AgentRequest, agent: Runnable = Depends(get_agent)):
    config = {"configurable": {"thread_id": body.thread_id}}

    async def event_generator():
        try:
            buffer = ""
            async for event in agent.astream_events(
                {"input": body.input},
                config=config,
                version="v2",
            ):
                kind = event["event"]
                tags = event.get("tags", [])
                if kind == "on_chat_model_stream" and "agent" in tags:
                    content = event["data"]["chunk"].content
                    buffer += content
                    if all(content not in seq for seq in STOP_SEQUENCES):
                        yield json.dumps(
                            {
                                "type": "agent",
                                "content": remove_stop_sequences(buffer),
                                "message_id": event["run_id"],
                            }
                        ) + "\n"
                        buffer = ""
                elif kind == "on_chat_model_stream" and "observer" in tags:
                    content = event["data"]["chunk"].content
                    yield json.dumps(
                        {
                            "type": "observer",
                            "content": content,
                            "message_id": event["run_id"],
                        }
                    ) + "\n"
                elif kind == "on_chat_model_stream" and "planner" in tags:
                    content = event["data"]["chunk"].content

                    yield json.dumps(
                        {
                            "type": "planner",
                            "content": content,
                            "message_id": event["run_id"],
                        }
                    ) + "\n"

                elif kind == "on_tool_start":
                    tool_input = event["data"].get("input")
                    if tool_input:
                        yield json.dumps(
                            {
                                "type": "tool_start",
                                "tool_id": event["run_id"],
                                "tool_name": event["name"],
                                "input": tool_input,
                            }
                        ) + "\n"

                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output")
                    yield json.dumps(
                        {
                            "type": "tool_end",
                            "tool_id": event["run_id"],
                            "tool_name": event["name"],
                            "output": tool_output,
                        }
                    ) + "\n"

                elif kind == "on_custom_event":
                    if event["name"] == "error":
                        error = event["data"]
                        yield json.dumps(
                            {
                                "type": "error",
                                "error": error,
                            }
                        ) + "\n"
                    if event["name"] == "tool_error":
                        tool_error = event["data"]
                        yield json.dumps(
                            {
                                "type": "tool_error",
                                "error": tool_error,
                            }
                        ) + "\n"
        except Exception as e:
            logging.error(f"Exception in event generator: {e}")
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/json")


@app.get("/get_tool_descriptions")
async def get_tool_descriptions():
    tools = get_tools()
    return tools.json
