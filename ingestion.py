"""Small, explicit ingestion helpers used by the API and the starter corpus loader."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from langchain_core.documents import Document
from pypdf import PdfReader

from config import settings

ALLOWED_TYPES = {
    ".pdf": {"application/pdf"}, ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"}, ".html": {"text/html"}, ".htm": {"text/html"},
}


class TextCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


@dataclass(frozen=True)
class UploadedContent:
    filename: str
    extension: str
    content_type: str
    content: bytes


async def read_and_validate_upload(file: UploadFile) -> UploadedContent:
    """Read a bounded upload once; the caller can then extract it without surprises."""
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    content_type = (file.content_type or "").lower()
    if extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Supported files: PDF, TXT, Markdown, and HTML.")
    if content_type and content_type not in ALLOWED_TYPES[extension]:
        raise HTTPException(status_code=415, detail="The file extension and content type do not match.")
    content = await file.read(settings.max_file_size_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="Files must be 10 MiB or smaller.")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF.")
    return UploadedContent(filename, extension, content_type, content)


def extract_text(upload: UploadedContent) -> str:
    """Keep file parsing here so the API route remains easy to follow."""
    if upload.extension == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(upload.content)).pages)
    else:
        text = upload.content.decode("utf-8", errors="replace")
        if upload.extension in {".html", ".htm"}:
            parser = TextCollector()
            parser.feed(text)
            text = "\n".join(parser.parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise HTTPException(status_code=422, detail="No readable text was found in this file.")
    return text


def split_text(text: str) -> list[str]:
    """Prefer paragraph boundaries, then overlap chunks for cross-section context."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > settings.chunk_size:
            chunks.append(current)
            current = current[-settings.chunk_overlap:] + "\n\n" + paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks


def make_documents(text: str, source_name: str, source_url: str | None = None) -> tuple[str, list[Document]]:
    digest = hashlib.sha256(f"{source_name}:{text}".encode()).hexdigest()[:12]
    identifier = f"doc_{digest}"
    documents = []
    for index, chunk in enumerate(split_text(text)):
        metadata: dict[str, Any] = {"document_id": identifier, "source_name": source_name, "chunk_index": index}
        if source_url:
            metadata["source_url"] = source_url
        documents.append(Document(page_content=chunk, metadata=metadata, id=str(uuid4())))
    return identifier, documents
