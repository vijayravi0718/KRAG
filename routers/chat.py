from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

# from backend.services.rag import rag_chat
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
    history = [
        {
            "role": m.role,
            "content": m.content,
        }
        for m in req.history
    ]

    return rag_chat(req.query, history)