from fastapi import FastAPI, HTTPException
from httpx import ConnectError

from ingestion_api import router as ingestion_router
from schemas import FeedbackRequest, QueryRequest, QueryResponse, Source
from store import list_documents, save_feedback
from workflow import rag_workflow

app = FastAPI(title="Technical Documentation Assistant", version="0.1.0")
app.include_router(ingestion_router)


@app.post("/query", response_model=QueryResponse, tags=["question answering"])
def query(request: QueryRequest) -> QueryResponse:
    if not list_documents():
        raise HTTPException(status_code=409, detail="No documents are indexed yet. Use POST /ingest first.")
    try:
        result = rag_workflow.invoke({"question": request.question, "retries": 0})
    except ConnectError as error:
        raise HTTPException(status_code=503, detail="Ollama is unavailable. Start it, then retry the request.") from error
    sources = [Source(document_id=document.metadata["document_id"], source_name=document.metadata["source_name"], location=document.metadata.get("source_url"), chunk_index=document.metadata["chunk_index"]) for document in result.get("relevant_documents", [])]
    return QueryResponse(answer=result["answer"], sources=sources, retries_used=result.get("retries", 0))


@app.get("/documents", tags=["documents"])
def documents() -> list[dict]:
    return list_documents()


@app.post("/feedback", status_code=201, tags=["feedback"])
def feedback(request: FeedbackRequest) -> dict[str, str]:
    save_feedback(request.model_dump())
    return {"message": "Thanks — your feedback was recorded."}
