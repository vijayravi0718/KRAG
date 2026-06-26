from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routers import documents, chat, health

app = FastAPI(title="Knowledge RAG API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173"), "*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://project-9mtrs.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api/documents")
app.include_router(chat.router, prefix="/api/chat")
