"""Layer 4 — Framework: live metrics dashboard at /dashboard and JSON stats at /api/stats."""
from __future__ import annotations
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

_TEMPLATE = (Path(__file__).resolve().parent.parent / "templates" / "dashboard.html").read_text(encoding="utf-8")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return _TEMPLATE


@router.get("/api/stats")
async def api_stats(request: Request) -> dict:
    return request.app.state.metrics.get_stats()
