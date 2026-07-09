"""
Memory — RAG Retrieval

Semantic search over unstructured business documents using pgvector.
Documents are embedded on ingestion and retrieved via cosine similarity.

Usage:
    # Index a document
    await index_document("meeting_2024_01_15", "We decided to focus on B2B SaaS...")

    # Retrieve relevant context
    results = await retrieve_context("what did we decide about pricing?", top_k=3)
"""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select, text
from db.connection import get_db
from db.models import MemoryLong

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


async def embed_text(text_content: str) -> list[float]:
    """
    Generate an embedding vector for a text string using OpenAI.

    Args:
        text_content: Text to embed

    Returns:
        Embedding vector as list of floats
    """
    client = AsyncOpenAI()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_content,
    )
    return response.data[0].embedding


async def index_document(
    key: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Index a document into long-term memory with its embedding.

    Args:
        key: Unique document identifier
        content: Document text content
        metadata: Optional metadata dict (stored as JSON in value field)
    """
    import json

    embedding = await embed_text(content)

    value_data = {"content": content, "metadata": metadata or {}}

    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = json.dumps(value_data)
            existing.embedding = embedding
        else:
            db.add(
                MemoryLong(
                    key=key,
                    value=json.dumps(value_data),
                    embedding=embedding,
                )
            )

        await db.commit()
    logger.info(f"Indexed document '{key}' ({len(content)} chars)")


async def retrieve_context(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Retrieve the most semantically relevant documents for a query.

    Args:
        query: Search query text
        top_k: Maximum number of results to return
        similarity_threshold: Minimum cosine similarity score (0–1)

    Returns:
        List of dicts with 'key', 'content', 'similarity', 'metadata'
    """
    import json

    query_embedding = await embed_text(query)

    async with get_db() as db:
        # pgvector cosine similarity search
        result = await db.execute(
            text(
                """
                SELECT key, value,
                       1 - (embedding <=> :embedding::vector) AS similarity
                FROM memory_long
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> :embedding::vector) >= :threshold
                ORDER BY similarity DESC
                LIMIT :top_k
                """
            ),
            {
                "embedding": str(query_embedding),
                "threshold": similarity_threshold,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()

    results = []
    for row in rows:
        try:
            value_data = json.loads(row.value)
            content = value_data.get("content", row.value)
            metadata = value_data.get("metadata", {})
        except (json.JSONDecodeError, TypeError):
            content = row.value
            metadata = {}

        results.append(
            {
                "key": row.key,
                "content": content,
                "similarity": float(row.similarity),
                "metadata": metadata,
            }
        )

    return results
