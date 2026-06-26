import os
from typing import List, Dict, Any

from fastapi import HTTPException
from openai import OpenAI

from backend.services.vectordb import search

MODEL = "gpt-4o-mini"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def build_context(chunks: List[Dict[str, Any]]) -> str:
    parts = []

    for i, c in enumerate(chunks):
        parts.append(
            f'<source index="{i+1}" doc="{c["doc_name"]}" score="{c["score"]}">\n'
            f'{c["text"]}\n'
            f'</source>'
        )

    return "\n\n".join(parts)


def rag_chat(query: str, history: List[Dict] = []):
    try:

        chunks = search(query, top_k=6)

        has_context = len(chunks) > 0

        if has_context:

            context = build_context(chunks)

            system_prompt = f"""
You are Knowledge, a RAG-powered AI assistant.

Answer ONLY using the retrieved context.

<retrieved_context>

{context}

</retrieved_context>
"""

        else:

            system_prompt = """
You are Knowledge AI.

No matching documents were found.

Tell the user that nothing relevant exists in the knowledge base.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(history[-10:])

        messages.append(
            {
                "role": "user",
                "content": query
            }
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content or ""

        return {
            "answer": answer,
            "has_context": has_context,
            "source_count": len(chunks),
            "sources": chunks,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )