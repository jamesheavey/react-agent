import os
import sys

sys.path.append(os.getcwd())
from dotenv import load_dotenv
from pymilvus import DataType, FieldSchema
from api.milvus.milvus import Milvus
from utils import (
    get_text_from_webpage,
    generate_id,
    extract_text_from_pdf,
    extract_text_from_docx,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from urls import urls

load_dotenv()


DIMENSION = 768
COLLECTION = os.getenv("MILVUS_COLLECTION")

# Set up Milvus
milvus = Milvus(cert_path="api/certs/cert.pem")

if COLLECTION in milvus.client.list_collections():
    milvus.client.drop_collection(COLLECTION)
    print("Collection dropped")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="chunk_number", dtype=DataType.INT64),
]

milvus.create_collection(
    collection_name=COLLECTION,
    fields=fields,
    index_field_name="vector",
    index_type="IVF_FLAT",
    metric_type="L2",
    nlist=1024,
)

print("Collection created")

metadata = []

if os.path.exists("scripts/data"):
    for file in os.listdir("scripts/data"):
        if file.endswith(".pdf"):
            text = extract_text_from_pdf(f"scripts/data/{file}")
        if file.endswith(".txt"):
            text = open(f"scripts/data/{file}", "r").read()
        if file.endswith(".docx"):
            text = extract_text_from_docx(f"scripts/data/{file}")

        text_chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)(text, 100)
        for n, chunk in enumerate(text_chunks):
            metadata.append({"source": file, "chunk_number": n, "text": chunk, "id": generate_id()})


for url in urls:
    text = get_text_from_webpage(url)
    text_chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20).split_text(text)
    for n, chunk in enumerate(text_chunks):
        metadata.append({"source": url, "chunk_number": n, "id": generate_id(), "text": chunk})

milvus.insert(collection_name=COLLECTION, metadata=metadata, progress_bar=True)

print("Data inserted")
