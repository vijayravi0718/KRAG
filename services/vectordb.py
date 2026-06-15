"""
ChromaDB Vector Database Service
Persistent storage with sentence-transformers embeddings.
Azure-ready: swap ChromaDB for Azure AI Search later with same interface.
"""

import os
import uuid
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "knowledge_base"
EMBED_MODEL = "all-MiniLM-L6-v2"


def _get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(chunks: List[Dict[str, Any]]) -> int:
    collection = _get_collection()
    ids, docs, metas = [], [], []
    for c in chunks:
        ids.append(str(uuid.uuid4()))
        docs.append(c["text"])
        metas.append({
            "doc_id":      c["doc_id"],
            "doc_name":    c["doc_name"],
            "source":      c.get("source", ""),
            "type":        c.get("type", "text"),
            "chunk_index": c["chunk_index"],
        })
    collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(ids)


def search(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    collection = _get_collection()
    if collection.count() == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":        doc,
            "doc_name":    meta["doc_name"],
            "doc_id":      meta["doc_id"],
            "source":      meta["source"],
            "type":        meta["type"],
            "chunk_index": meta["chunk_index"],
            "score":       round(1 - dist, 4),
        })
    return sorted(chunks, key=lambda x: x["score"], reverse=True)


def delete_document(doc_id: str) -> int:
    collection = _get_collection()
    results = collection.get(where={"doc_id": doc_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])
    return len(results["ids"])


def list_documents() -> List[Dict[str, Any]]:
    collection = _get_collection()
    if collection.count() == 0:
        return []
    all_data = collection.get(include=["metadatas"])
    docs: Dict[str, Dict] = {}
    for meta in all_data["metadatas"]:
        did = meta["doc_id"]
        if did not in docs:
            docs[did] = {
                "doc_id":      did,
                "doc_name":    meta["doc_name"],
                "source":      meta["source"],
                "type":        meta["type"],
                "chunk_count": 0,
            }
        docs[did]["chunk_count"] += 1
    return list(docs.values())


def get_stats() -> Dict[str, Any]:
    collection = _get_collection()
    return {
        "total_chunks": collection.count(),
        "total_docs":   len(list_documents()),
        "embed_model":  EMBED_MODEL,
    }


def clear_all():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    client.delete_collection(COLLECTION_NAME)
