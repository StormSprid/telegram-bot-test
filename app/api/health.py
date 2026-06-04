"""Layer 4 — Framework: health-check endpoint."""
from __future__ import annotations
import os

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    state = request.app.state
    return {
        "status": "ok",
        "env": os.getenv("APP_ENV", "development"),
        "model": state.settings.llm_model,
        "knowledge_docs": state.knowledge_document_count,
        "stream_enabled": state.settings.stream_enabled,
    }
