from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
# from services.ingest import ingest_file, ingest_url, ingest_text
# from services.vectordb import list_documents, delete_document, get_stats, clear_all
from backend.services.ingest import ingest_file, ingest_url, ingest_text
from backend.services.vectordb import (
    list_documents,
    delete_document,
    get_stats,
)
router = APIRouter()


class URLRequest(BaseModel):
    url: str


class TextRequest(BaseModel):
    title: str
    text: str


@router.get("/")
def get_documents():
    return {"documents": list_documents(), "stats": get_stats()}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    result = await ingest_file(file.filename, contents)
    return result


@router.post("/url")
async def add_url(req: URLRequest):
    try:
        result = await ingest_url(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/text")
async def add_text(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    result = await ingest_text(req.title, req.text)
    return result


@router.delete("/{doc_id}")
def remove_document(doc_id: str):
    count = delete_document(doc_id)
    return {"deleted_chunks": count}


@router.delete("/")
def clear_documents():
    clear_all()
    return {"message": "All documents cleared"}
