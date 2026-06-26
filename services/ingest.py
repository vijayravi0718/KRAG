"""
Ingestion Service — extract text from PDF, URL, CSV, JSON, plain text.
Then chunk and store in ChromaDB.
"""

import io
import uuid
import httpx
import pandas as pd
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from typing import List, Dict, Any
# from services.vectordb import add_chunks
from services.vectordb import add_chunks


# ── Chunking ──────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    chunks = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            i = 0
            while i < len(para):
                chunk = para[i: i + chunk_size].strip()
                if len(chunk) > 30:
                    chunks.append(chunk)
                i += chunk_size - overlap
    if not chunks and text.strip():
        chunks = [text.strip()]
    return chunks


def store_chunks(chunks: List[str], doc_id: str, doc_name: str, source: str, doc_type: str) -> int:
    records = [
        {
            "text":        c,
            "doc_id":      doc_id,
            "doc_name":    doc_name,
            "source":      source,
            "type":        doc_type,
            "chunk_index": i,
        }
        for i, c in enumerate(chunks)
    ]
    return add_chunks(records)


# ── Extractors ────────────────────────────────────────────
def extract_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages)


def extract_csv(file_bytes: bytes) -> str:
    df = pd.read_csv(io.BytesIO(file_bytes))
    rows = []
    for _, row in df.iterrows():
        rows.append(" | ".join(f"{col}: {val}" for col, val in row.items()))
    return f"Columns: {', '.join(df.columns)}\n\n" + "\n".join(rows)


def extract_json(file_bytes: bytes) -> str:
    import json
    data = json.loads(file_bytes)
    def flatten(obj, prefix=""):
        if isinstance(obj, list):
            return "\n".join(flatten(item, f"{prefix}[{i}]") for i, item in enumerate(obj[:50]))
        if isinstance(obj, dict):
            return "\n".join(flatten(v, f"{prefix}.{k}" if prefix else k) for k, v in obj.items())
        return f"{prefix}: {obj}"
    return flatten(data)


async def extract_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────
async def ingest_file(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        text = extract_pdf(file_bytes)
        doc_type = "pdf"
    elif ext == "csv":
        text = extract_csv(file_bytes)
        doc_type = "csv"
    elif ext == "json":
        text = extract_json(file_bytes)
        doc_type = "json"
    else:
        text = file_bytes.decode("utf-8", errors="replace")
        doc_type = "text"

    doc_id = str(uuid.uuid4())
    chunks = chunk_text(text)
    count = store_chunks(chunks, doc_id, filename, filename, doc_type)
    return {"doc_id": doc_id, "doc_name": filename, "chunk_count": count, "type": doc_type}


async def ingest_url(url: str) -> Dict[str, Any]:
    text = await extract_url(url)
    doc_id = str(uuid.uuid4())
    doc_name = url.split("//")[-1].split("/")[0]
    chunks = chunk_text(text)
    count = store_chunks(chunks, doc_id, doc_name, url, "url")
    return {"doc_id": doc_id, "doc_name": doc_name, "chunk_count": count, "type": "url"}


async def ingest_text(title: str, text: str) -> Dict[str, Any]:
    doc_id = str(uuid.uuid4())
    chunks = chunk_text(text)
    count = store_chunks(chunks, doc_id, title, "manual", "text")
    return {"doc_id": doc_id, "doc_name": title, "chunk_count": count, "type": "text"}
