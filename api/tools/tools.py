import os
import re
import json
import numexpr as ne
from langchain_core.tools import tool
from datetime import datetime
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonAstREPLTool
from utils import format_tools
from milvus.milvus import Milvus
from utils import is_rag_enabled

"""
This file contains the tools for the agent.

To create a new tool, create a new function with the @tool decorator, and add a description.

To add the tool to the agent, add it to the get_tools function.
"""

################################################################################


def get_tools():
    """
    Get all the tools for the agent.

    Update the tool list as needed.
    """

    tools = [
        run_python,
        calculator,
        current_datetime,
        search,
    ]
    
    if is_rag_enabled():
        tools.append(get_context)

    return format_tools(tools)


################################################################################


@tool
def calculator(expression: str):
    """
    Use this tool for mathematical calculations/expressions. Do not do any calculations on your own.
    It requires python `numexpr` syntax. Be sure syntax is correct. Only use expressions that can be evaluated by `numexpr`.

    Example:
    expression = 2 + 2
    result = 4
    """
    expression = expression.replace("^", "**").replace('"', "")
    return ne.evaluate(expression).item()


@tool
def current_datetime(none=""):
    """
    This is a tool to get the current date/time.

    Example:
    result = 2024-01-01 12:00:00
    """
    return str(datetime.now())


@tool
def search(query: str):
    """
    Use this tool to search for information. It requires a search query and returns a summary of the results.

    Example:
    query = what is the capital of france?
    result = Paris
    """
    # TODO: switch Wikipedia to Google Search/DuckDuckGo Search
    if os.getenv("TAVILY_API_KEY"):
        tavily = TavilySearchResults()
        results = tavily.invoke(query)
        content = [result["content"] for result in results]
        return "\n".join(content)
    else:
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wikipedia.run(query)


@tool
def run_python(code_string: str):
    """
    Use this tool to run python code. Input should be valid python code in string format.
    It requires a python code and returns the output of the code.
    Print any variables you want to see the output of, return will not work you must print.
    Use " for the external quotes and ' inside of the code string.

    Example:
    code_string = "def factorial(n):
        if n == 0:
            return 1
        else:
            return n * factorial(n-1)

    result = factorial(5)
    print(f'Factorial of 5 is {result}')"
    result = "Factorial of 5 is 120"
    """
    return PythonAstREPLTool().invoke(code_string.strip())


# This is a RAG tool, it is used to query Milvus for context about the users query.
# This will be automatically added to the agent if the MILVUS_HOST environment variable is set.
# Ensure that you describe the type of data available in Milvus in the tool description.


@tool
def get_context(query: str):
    """
    This is a tool to query Milvus for context about the users query.
    The Milvus DB only contains information about {DESCRIPTION OF DATASET}.

    Example:
    input = What is IBM?
    result = IBM is a multinational technology company headquartered in Armonk, New York.
    """
    milvus = Milvus(cert_path="certs/cert.pem")

    results = milvus.search(
        collection_name=os.getenv("MILVUS_COLLECTION"),
        query=query,
        k=5,
        output_fields=["text"],
    )
    return "\n".join([result["entity"]["text"] for result in results])
