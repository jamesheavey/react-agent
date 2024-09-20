import os
import chainlit as cl
import httpx
import uuid
import json
import asyncio
from utils import format_message, create_tool, get_tool_config, get_author
from dotenv import load_dotenv

load_dotenv()

AGENT_API_URL = os.getenv("AGENT_API_URL") or "http://localhost:8000"


@cl.on_chat_start
async def on_chat_start():
    if not cl.user_session.get("thread_id"):
        cl.user_session.set("thread_id", str(uuid.uuid4()))

    if not cl.user_session.get("tools"):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                AGENT_API_URL + "/get_tool_descriptions", timeout=30.0
            )
            tools = response.json()

            if isinstance(tools, str):
                try:
                    tools = json.loads(tools)
                except json.JSONDecodeError:
                    print("Error: Received an invalid response for tools")
                    return

            if isinstance(tools, list):
                cl.user_session.set(
                    "tools", "\n".join(["- " + tool["name"] for tool in tools])
                )
            else:
                print("Error: Tools should be a list of dictionaries")
                return

    intro_message = (
        "Hi, I am an agent powered by WatsonX to help you with your questions.\n\n"
        f"Here are the tools I have at my disposal: \n{cl.user_session.get('tools')}\n\n"
        "How can I help you today?"
    )
    intro = await cl.Message(content="", author="Agent").send()
    for i in range(0, len(intro_message), 6):
        intro.content = intro_message[:i]
        await intro.update()
        await asyncio.sleep(0.02)
    intro.content = intro_message
    await intro.update()


@cl.on_chat_resume
async def on_chat_resume(thread):
    initial_data = cl.user_session.get("thread_id")
    thread_id = thread.get("id", None)
    await cl.Message(
        content=f"Resumed chat session with thread ID: {thread_id}. Initial data: {initial_data}"
    ).send()


@cl.on_chat_start
async def on_chat_start():
    if not cl.user_session.get("thread_id"):
        cl.user_session.set("thread_id", str(uuid.uuid4()))

    if not cl.user_session.get("tools"):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                AGENT_API_URL + "/get_tool_descriptions", timeout=30.0
            )
            tools = response.json()

            if isinstance(tools, str):
                try:
                    tools = json.loads(tools)
                except json.JSONDecodeError:
                    print("Error: Received an invalid response for tools")
                    return

            if isinstance(tools, list):
                cl.user_session.set(
                    "tools", "\n".join(["- " + tool["name"] for tool in tools])
                )
            else:
                print("Error: Tools should be a list of dictionaries")
                return

    intro_message = (
        "Hi, I am an agent powered by WatsonX to help you with your questions.\n\n"
        f"Here are the tools I have at my disposal: \n{cl.user_session.get('tools')}\n\n"
        "How can I help you today?"
    )
    intro = await cl.Message(content="", author="Agent").send()
    for i in range(0, len(intro_message), 6):
        intro.content = intro_message[:i]
        await intro.update()
        await asyncio.sleep(0.02)
    intro.content = intro_message
    await intro.update()


@cl.on_chat_resume
async def on_chat_resume(thread):
    initial_data = cl.user_session.get("thread_id")
    thread_id = thread.get("id", None)
    await cl.Message(
        content=f"Resumed chat session with thread ID: {thread_id}. Initial data: {initial_data}"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    async with httpx.AsyncClient() as client:
        try:
            tools = {}
            messages = {}
            current_message_id = None
            current_tool_id = None
            plan = None

            async with client.stream(
                "POST",
                AGENT_API_URL + "/stream_agent",
                json={"input": message.content, "thread_id": thread_id},
                timeout=30.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        event = json.loads(line)

                        if event["type"] == "agent":
                            if event["message_id"] in messages:
                                message = messages[event["message_id"]]
                                message.author = get_author(message.content)
                                message.metadata["raw_content"] += event["content"]
                                message.content = format_message(
                                    message.metadata["raw_content"]
                                )
                                await message.update()
                            else:
                                author = get_author(event["content"])
                                message = cl.Message(
                                    content=format_message(event["content"]),
                                    metadata={"raw_content": event["content"]},
                                    author=author,
                                )
                                messages[event["message_id"]] = message
                                current_message_id = event["message_id"]
                                await message.send()

                        elif event["type"] == "observer":
                            if current_message_id in messages:
                                message = messages[current_message_id]
                                message.metadata["raw_content"] += event["content"]
                                message.content = format_message(
                                    message.metadata["raw_content"]
                                )
                                await message.update()

                        elif event["type"] == "planner":
                            if plan:
                                plan.metadata["raw_content"] += event["content"]
                                plan.content = format_message(
                                    plan.metadata["raw_content"]
                                )
                                await plan.update()
                            else:
                                plan = cl.Message(
                                    content=f"Plan:\n\n{format_message(event['content'])}",
                                    metadata={
                                        "raw_content": f"Plan:\n\n{event['content']}"
                                    },
                                    author="Plan",
                                )
                                await plan.send()

                        elif event["type"] == "tool_start":
                            tool_id = event["tool_id"]
                            current_tool_id = tool_id
                            tool = create_tool(event["tool_name"], event["input"])
                            tool_name, input_type = get_tool_config(event["tool_name"])
                            parent_message = messages[current_message_id]
                            tool_message = cl.Step(
                                type="tool",
                                id=tool_id,
                                name=tool_name,
                                show_input=input_type,
                                parent_id=parent_message.id,
                            )
                            tool_message.input = tool
                            await tool_message.send()
                            tools[tool_id] = tool_message

                        elif event["type"] == "tool_end":
                            tool_output = event["output"]
                            tool_id = event["tool_id"]
                            tool_message = tools.get(tool_id, None)
                            if tool_message:
                                tool_message.output = f"```text\n{tool_output}\n```"
                                await tool_message.update()

                        elif event["type"] == "tool_error":
                            tool_output = event["error"]
                            tool_id = current_tool_id
                            tool_message = tools.get(tool_id, None)
                            if tool_message:
                                tool_message.output = f"```text\n{tool_output}\n```"
                                await tool_message.update()

                        elif event["type"] == "error":
                            error = event["error"]
                            await cl.Message(
                                content=f"**Error:** {error}",
                                author="Error",
                                parent_id=current_message_id,
                            ).send()

        except Exception as e:
            await cl.Message(content=f"Error: {e}", author="Error").send()
            raise e
