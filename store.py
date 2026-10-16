"""Persistence boundary for Chroma and the small document/feedback registries."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from config import settings


def _registry_path() -> Path:
    settings.data_dir.mkdir(exist_ok=True)
    return settings.data_dir / "documents.json"


def get_vector_store() -> Chroma:
    settings.data_dir.mkdir(exist_ok=True)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=OllamaEmbeddings(model=settings.embedding_model),
        persist_directory=str(settings.data_dir / "chroma"),
    )


def list_documents() -> list[dict[str, Any]]:
    path = _registry_path()
    return json.loads(path.read_text()) if path.exists() else []


def index_documents(document_id: str, source_name: str, documents: list, source_url: str | None = None) -> None:
    vector_store = get_vector_store()
    # Replacing a document keeps re-uploaded source material from going stale.
    vector_store.delete(where={"document_id": document_id})
    vector_store.add_documents(documents)
    records = [item for item in list_documents() if item["document_id"] != document_id]
    records.append({"document_id": document_id, "source_name": source_name, "source_url": source_url, "chunk_count": len(documents), "indexed_at": datetime.now(UTC).isoformat()})
    _registry_path().write_text(json.dumps(records, indent=2), encoding="utf-8")


def save_feedback(record: dict[str, Any]) -> None:
    settings.data_dir.mkdir(exist_ok=True)
    record["submitted_at"] = datetime.now(UTC).isoformat()
    with (settings.data_dir / "feedback.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")
