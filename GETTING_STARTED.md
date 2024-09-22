# Getting Started

## Contents

- [Getting Started](#getting-started)
  - [Contents](#contents)
  - [Guide](#guide)
    - [Environment variables](#environment-variables)
    - [Run the API Locally](#run-the-api-locally)
    - [Run the API with Chainlit UI](#run-the-api-with-chainlit-ui)
    - [Adding new tools](#adding-new-tools)
    - [RAG Tool / Milvus](#rag-tool--milvus)
      - [Loading your own data](#loading-your-own-data)
      - [Adding the RAG tool to the agent](#adding-the-rag-tool-to-the-agent)


## Guide

### Environment variables

A `.env.example` file is provided within the `react-agent` directory. Copy this file to `.env` and fill in the required variables.
(You must provide an OpenAI or Anthropic api key, all other variables are optional)


### Run the API Locally

To run the FastAPI application locally:

1. Create a virtual environment, install the requirements

```bash
make setup
```

2. Run the FastAPI application

```bash
make start-api
```

3. You can now access the APIs at the URL

```bash
http://localhost:8000/docs
```

### Run the API with Chainlit UI

To run the FastAPI application with Chainlit UI locally:

1. Create a virtual environment, install the requirements

```bash
make setup
```

2. Run the FastAPI + Chainlit UI application

```bash
make start
```

3. Interface with the agent via the Chainlit UI at the URL:

```bash
http://localhost:8001
```

### Adding new tools

To add a new tool, you need to add it to the `api/tools/tools.py` file in the following format:

```python
@tool
def new_tool(input: <type>) -> <type>:
    "This is a description of the tool for the LLM"
    <code to execute>
    return <value>
```

Then simply add the function name to the `get_tools` function list in the same file.

You can also import prebuilt tools from `langchain_community.tools` and add them to the tools list in the same way.


### RAG Tool / Milvus

There is a prebuilt RAG tool template for for Milvus.
To use it, you need to provide a valid set of Milvus connection environment variables, see `.env.example` for the required variables.


#### Loading your own data

If your data is not in Milvus, you can load it into Milvus using the `make create_db` script.

Simply add any webpage urls into the list in `scripts/urls.py`, or add any `.pdf`, `.txt`, `.docx` files into the `scripts/data` folder.

Then run the `create_db.py` script, which will chunk the data and load it into Milvus.

If you want to customise the data loading, you can modify the `create_db.py` script.


#### Adding the RAG tool to the agent

Once the data is loaded into Milvus and the environment variables are added, the `get_context` tool will automatically be added to the agent.

The base tool looks like this:

```python
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

    results = milvus.search(collection_name=os.getenv("MILVUS_COLLECTION"), query=query, k=5, output_fields=["text"])

    return [result["entity"]["text"] for result in results]
```

You should modify the description, replacing `{DESCRIPTION OF DATASET}` to include details about the dataset you have loaded into Milvus so that the LLM can understand when to use the tool.
