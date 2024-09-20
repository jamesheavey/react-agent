import os
from dotenv import load_dotenv
from pymilvus import MilvusClient, utility, connections, FieldSchema, CollectionSchema
from fastapi import HTTPException
from typing import Any, Dict, List
from langchain_huggingface import HuggingFaceEmbeddings
import logging
import math


load_dotenv()


class Milvus:
    def __init__(
        self,
        host: str = os.environ.get("MILVUS_HOST", None),
        port: str = os.environ.get("MILVUS_PORT", None),
        user: str = os.environ.get("MILVUS_USER", None),
        password: str = os.environ.get("MILVUS_PASSWORD", None),
        cert_path: str = "./cert.pem",
        secure: bool = (True if os.environ.get("MILVUS_SECURE", "false").lower() == "true" else False),
        server_name: str = "localhost",
        embedding_model_id: str = "ibm/slate-125m-english-rtrvr",
        timeout: int = 10,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.secure = secure
        self.server_pem_path = cert_path
        self.server_name = server_name
        self.uri = f"http{'s' if self.secure else ''}://{self.user}:{self.password}@{self.host}:{self.port}"
        self.timeout = timeout
        self._connect()
        self.client = self._get_milvus_client()
        self.embedding_model_id = embedding_model_id
        self.embeddings = HuggingFaceEmbeddings()

    def _get_milvus_client(self):
        client = MilvusClient(
            uri=self.uri,
            secure=self.secure,
            server_name=self.server_name,
            server_pem_path=self.server_pem_path,
            timeout=self.timeout,
        )
        logging.info(f"Milvus server version: {utility.get_server_version()}")
        return client

    def _connect(self):
        connections.connect(
            uri=self.uri,
            secure=self.secure,
            server_name=self.server_name,
            server_pem_path=self.server_pem_path,
        )

    def create_collection(
        self,
        collection_name: str,
        fields: List[FieldSchema],
        index_field_name: str,
        index_type: str = "IVF_FLAT",
        metric_type: str = "L2",
        nlist: int = 1024,
        auto_id: bool = False,
        id_field_name: str = "id",
        id_type: str = "int",
    ):
        schema = CollectionSchema(fields=fields, auto_id=auto_id, enable_dynamic_field=False)

        index_params = self.client.prepare_index_params(
            field_name=index_field_name,
            index_type=index_type,
            metric_type=metric_type,
            params={"nlist": nlist},
        )

        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
            dimension=next((field.dim for field in fields if field.dim), None),
            auto_id=auto_id,
            id_type=id_type,
            vector_field_name=index_field_name,
            primary_field_name=id_field_name,
            metric_type=metric_type,
        )

    def insert(
        self,
        collection_name: str,
        text_field_name: str = "text",
        vector_field_name: str = "vector",
        metadata: List[Dict[str, Any]] = [{}],
        progress_bar: bool = True,
    ):
        text_fields = [item[text_field_name] for item in metadata]
        embedded_vectors = self.embeddings.embed_documents(text_fields)
        for item, vector in zip(metadata, embedded_vectors):
            item[vector_field_name] = vector
        self.client.insert(collection_name=collection_name, data=metadata, progress_bar=progress_bar)

    @staticmethod
    def distance_to_score(dist, decay_rate=1.0):
        similarity_score = math.exp(-decay_rate * dist)
        return round(similarity_score, 2)

    def search(
        self,
        collection_name: str,
        query: str,
        filter: str = None,
        k: int = 10,
        search_params: Dict[str, Any] = {"metric_type": "L2", "params": {"nprobe": 10}},
        output_fields: List[str] = None,
        **kwargs,
    ):

        res = self.client.search(
            collection_name=collection_name,
            data=[self.embeddings.embed_query(query)],
            limit=k,
            search_params=search_params,
            output_fields=output_fields,
            filter=filter,
            **kwargs,
        )

        for hit in res[0]:
            hit["score"] = self.distance_to_score(hit["distance"])

        return res[0]

    def query(
        self,
        collection_name: str,
        expr: str = "",
        k: int = 10,
        output_fields: List[str] = None,
        **kwargs,
    ):
        docs = self.client.query(
            collection_name=collection_name,
            filter=expr,
            limit=k,
            output_fields=output_fields,
            **kwargs,
        )

        if not docs:
            raise HTTPException(detail="Document not found", status_code=404)

        return docs

    def get(self, collection_name: str, id: int, output_fields: List[str]):
        docs = self.client.get(collection_name, id, output_fields)
        if not docs:
            raise HTTPException(detail="Document not found", status_code=404)
        return docs
