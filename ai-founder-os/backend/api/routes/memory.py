"""
API Route — /api/memory

"Company Brain" inspection endpoints.
Browse, search, and update long-term memory entries.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.schemas import (
    MemoryEntry,
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    MemoryUpsertRequest,
)
from db.connection import get_db
from db.models import MemoryLong
from memory.retrieval import retrieve_context, index_document
from memory.long_term import save_memory

router = APIRouter()


@router.get("/", response_model=list[MemoryEntry])
async def list_memory_entries(limit: int = 50):
    """List all long-term memory entries (most recently updated first)."""
    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong)
            .order_by(MemoryLong.updated_at.desc())
            .limit(limit)
        )
        entries = result.scalars().all()

    return [
        MemoryEntry(
            key=e.key,
            value=e.value,
            updated_at=e.updated_at,
        )
        for e in entries
    ]


@router.get("/{key}", response_model=MemoryEntry)
async def get_memory_entry(key: str):
    """Get a specific memory entry by key."""
    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail=f"Memory key '{key}' not found")

    return MemoryEntry(key=entry.key, value=entry.value, updated_at=entry.updated_at)


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(body: MemorySearchRequest):
    """
    Semantic search over the company brain using RAG retrieval.
    
    Uses pgvector cosine similarity to find relevant memory entries.
    """
    results = await retrieve_context(
        query=body.query,
        top_k=body.top_k,
        similarity_threshold=body.similarity_threshold,
    )

    return MemorySearchResponse(
        query=body.query,
        results=[
            MemorySearchResult(
                key=r["key"],
                content=r["content"],
                similarity=r["similarity"],
                metadata=r["metadata"],
            )
            for r in results
        ],
    )


@router.put("/{key}", response_model=MemoryEntry)
async def upsert_memory_entry(key: str, body: MemoryUpsertRequest):
    """
    Create or update a long-term memory entry.
    Also re-indexes the embedding for RAG retrieval.
    """
    await index_document(key=key, content=body.value)

    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=500, detail="Failed to upsert memory entry")

    return MemoryEntry(key=entry.key, value=entry.value, updated_at=entry.updated_at)


@router.delete("/{key}")
async def delete_memory_entry(key: str):
    """Delete a long-term memory entry by key."""
    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        entry = result.scalar_one_or_none()

        if entry is None:
            raise HTTPException(status_code=404, detail=f"Memory key '{key}' not found")

        await db.delete(entry)
        await db.commit()

    return {"message": f"Memory entry '{key}' deleted"}
