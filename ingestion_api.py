from typing import Annotated
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ingestion import UploadedContent, extract_text, make_documents, read_and_validate_upload
from store import index_documents

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/", status_code=201)
async def ingest_documents(
    files: Annotated[list[UploadFile] | None, File(description="PDF, TXT, Markdown, or HTML files")] = None,
    urls: Annotated[list[str] | None, Form(description="Public URLs to ingest")] = None,
) -> dict:
    if not files and not urls:
        raise HTTPException(status_code=422, detail="Provide at least one file or URL.")
    indexed: list[dict] = []
    for file in files or []:
        upload = await read_and_validate_upload(file)
        identifier, documents = make_documents(extract_text(upload), upload.filename)
        index_documents(identifier, upload.filename, documents)
        indexed.append({"document_id": identifier, "source_name": upload.filename, "chunk_count": len(documents)})
    for url in urls or []:
        try:
            request = Request(url, headers={"User-Agent": "ExpressAnalyticsRAG/1.0"})
            with urlopen(request, timeout=15) as response:  # nosec B310: explicit ingestion feature, not a server-side crawler
                content, content_type = response.read(), response.headers.get_content_type()
        except (URLError, ValueError) as error:
            raise HTTPException(status_code=422, detail=f"Could not fetch {url}: {error}") from error
        if content_type not in {"text/plain", "text/html", "text/markdown"}:
            raise HTTPException(status_code=415, detail=f"{url} is not a text or HTML document.")
        upload = UploadedContent(url, ".html" if content_type == "text/html" else ".txt", content_type, content)
        identifier, documents = make_documents(extract_text(upload), url, source_url=url)
        index_documents(identifier, url, documents, source_url=url)
        indexed.append({"document_id": identifier, "source_name": url, "chunk_count": len(documents)})
    return {"indexed": indexed}
