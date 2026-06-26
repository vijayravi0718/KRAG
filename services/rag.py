# """
# RAG Pipeline — retrieves chunks from ChromaDB and calls OpenAI API.
# Changed from Anthropic: pip install openai, update .env with OPENAI_API_KEY
# """

# import os
# from openai import OpenAI
# from typing import List, Dict, Any
# from services.vectordb import search

# MODEL = "gpt-4o"   # or "gpt-4o-mini" for cheaper
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# def build_context(chunks: List[Dict[str, Any]]) -> str:
#     parts = []
#     for i, c in enumerate(chunks):
#         parts.append(
#             f'<source index="{i+1}" doc="{c["doc_name"]}" score="{c["score"]}">\n{c["text"]}\n</source>'
#         )
#     return "\n\n".join(parts)


# def rag_chat(query: str, history: List[Dict] = []) -> Dict[str, Any]:
#     chunks = search(query, top_k=6)
#     has_context = len(chunks) > 0

#     if has_context:
#         context = build_context(chunks)
#         system_prompt = f"""You are Knowledge, a RAG-powered AI assistant.
# Answer questions using ONLY the retrieved context below.
# Be accurate, cite document names naturally in your answer.
# If context is insufficient, say so clearly.

# <retrieved_context>
# {context}
# </retrieved_context>"""
#     else:
#         system_prompt = """You are Knowledge, an AI assistant.
# No relevant documents were found in the knowledge base for this query.
# Inform the user politely and suggest they add relevant documents.
# You may still answer with general knowledge if appropriate."""

#     messages = [{"role": "system", "content": system_prompt}]
#     messages += history[-10:]
#     messages.append({"role": "user", "content": query})

#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=messages,
#         max_tokens=1024,
#         temperature=0.3,
#     )

#     answer = response.choices[0].message.content or ""

#     return {
#         "answer":       answer,
#         "has_context":  has_context,
#         "source_count": len(chunks),
#         "sources":      chunks,
#         "model":        response.model,
#         "usage": {
#             "input_tokens":  response.usage.prompt_tokens,
#             "output_tokens": response.usage.completion_tokens,
#         },
#     }
from fastapi import HTTPException
import traceback

...

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.3,
    )
except Exception as e:
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=str(e))