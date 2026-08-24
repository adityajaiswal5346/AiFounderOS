"""
API — Pydantic Schemas

Request and response models for all API routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Digest ─────────────────────────────────────────────────────────────────────

class DigestResponse(BaseModel):
    run_id: str
    date: str
    markdown: str
    pending_approval_count: int
    created_at: datetime


class DigestListItem(BaseModel):
    run_id: str
    date: str
    pending_approval_count: int
    created_at: datetime


# ── Approvals ─────────────────────────────────────────────────────────────────

class ApprovalItem(BaseModel):
    id: str
    task_id: Optional[str] = None
    tool_name: str
    description: str
    payload: Any
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    reviewed_by: Optional[str] = None


class ApprovalListResponse(BaseModel):
    items: list[ApprovalItem]
    total: int


# ── Memory ────────────────────────────────────────────────────────────────────

class MemoryEntry(BaseModel):
    key: str
    value: Any
    updated_at: datetime


class MemorySearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class MemorySearchResult(BaseModel):
    key: str
    content: str
    similarity: float
    metadata: dict[str, Any] = {}


class MemorySearchResponse(BaseModel):
    query: str
    results: list[MemorySearchResult]


class MemoryUpsertRequest(BaseModel):
    key: str
    value: str


# ── Roadmap ───────────────────────────────────────────────────────────────────

class RoadmapItem(BaseModel):
    title: str
    status: str  # built, planned, stub
    notes: Optional[str] = None


class RoadmapSection(BaseModel):
    section: str
    items: list[RoadmapItem]


class RoadmapResponse(BaseModel):
    sections: list[RoadmapSection]
    last_updated: str


# ── Tasks ─────────────────────────────────────────────────────────────────────

class TaskItem(BaseModel):
    id: str
    run_id: str
    agent: str
    description: str
    status: str
    priority: int = 1
    requires_approval: bool = False
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskCreateRequest(BaseModel):
    agent_name: str
    title: str
    description: Optional[str] = None


class TaskListResponse(BaseModel):
    items: list[TaskItem]
    total: int

