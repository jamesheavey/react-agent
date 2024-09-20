from langchain_core.utils.function_calling import convert_to_openai_tool
from typing import List
from langchain_core.tools import BaseTool
import json
from dataclasses import dataclass
import os
from milvus.milvus import Milvus


@dataclass
class Tools:
    functions: List[BaseTool]
    json: str
    names: List[str]


def format_tools(tools: List[BaseTool]):
    return Tools(
        functions=tools,
        json=json.dumps([convert_to_openai_tool(tool)["function"] for tool in tools], indent=2),
        names=[tool.name for tool in tools],
    )


def is_rag_enabled():
    if not os.getenv("MILVUS_HOST"):
        return False
    try:
        milvus = Milvus(cert_path="certs/cert.pem")
        if milvus.client.has_collection(collection_name=os.getenv("MILVUS_COLLECTION")):
            return True
        else:
            print(f"RAG Disabled: Collection '{os.getenv('MILVUS_COLLECTION')}' does not exist or is empty.")
            return False
    except Exception as e:
        print(f"RAG Disabled: Failed to connect to Milvus: {e}")
        return False
