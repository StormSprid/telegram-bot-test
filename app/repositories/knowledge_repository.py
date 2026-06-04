"""Layer 3 — Interface Adapter: loads and parses the Markdown knowledge base into documents."""
from __future__ import annotations
from pathlib import Path

from app.schemas.models import KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load_documents(self) -> list[KnowledgeDocument]:
        text = self._path.read_text(encoding="utf-8")
        docs: list[KnowledgeDocument] = []
        for i, section in enumerate(text.split("## ")):
            section = section.strip()
            if not section:
                continue
            parts = section.split("\n", 1)
            title = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            if title:
                docs.append(KnowledgeDocument(id=f"doc_{i}", title=title, content=content))
        return docs
