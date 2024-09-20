import os
from pymongo import MongoClient
from langgraph.checkpoint.memory import MemorySaver
from mongo.mongo_saver import MongoDBSaver
from langchain_core.runnables.graph import CurveStyle
from langgraph.graph.state import CompiledStateGraph
import logging
from langchain_core.callbacks.manager import adispatch_custom_event
import asyncio
from typing import Any
import json


def get_checkpointer():
    mongo_host = os.getenv("MONGO_HOST")
    mongo_port = os.getenv("MONGO_PORT")

    if not mongo_host or not mongo_port:
        logging.info("Using default memory saver.")
        return MemorySaver()

    try:
        mongo_port = int(mongo_port)
        client = MongoClient(mongo_host, mongo_port)
        client.admin.command("ismaster")
        logging.info("Using MongoDB as checkpoint saver.")
        return MongoDBSaver(host=mongo_host, port=mongo_port, db_name="checkpoints")
    except Exception as e:
        logging.info(f"MongoDB connection failed: {e}. Using default memory saver.")
        return MemorySaver()


def render_graph(graph: CompiledStateGraph):
    try:
        graph.get_graph(xray=True).draw_mermaid_png(
            curve_style=CurveStyle.NATURAL,
            output_file_path="../assets/architecture.png",
        )
    except Exception as e:
        logging.error(f"Error rendering graph: {e}")


def send_event(event_name: str, event_data: Any):
    asyncio.run(adispatch_custom_event(event_name, event_data))


def state_to_string(state: dict) -> str:
    state_str = []

    for key, value in state.items():
        try:
            state_str.append(f"{key}: {json.dumps(value, default=str, indent=4)}")
        except (TypeError, ValueError):
            state_str.append(f"{key}: {str(value)}")

    return "\n".join(state_str)
