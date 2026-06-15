from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from services.rag import rag_chat

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    history: List[Message] = []


@router.post("/")
def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    result = rag_chat(req.query, history)
    return result
