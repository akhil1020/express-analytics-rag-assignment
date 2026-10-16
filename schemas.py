from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class Source(BaseModel):
    document_id: str
    source_name: str
    location: str | None = None
    chunk_index: int


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    retries_used: int


class FeedbackRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    answer: str = Field(min_length=1)
    helpful: bool
    comment: str | None = Field(default=None, max_length=1_000)
