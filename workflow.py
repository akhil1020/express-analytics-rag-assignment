"""The self-correcting RAG graph required by the assignment."""

from __future__ import annotations

from typing import Literal

from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from config import settings
from store import get_vector_store


class RAGState(TypedDict, total=False):
    question: str
    search_query: str
    retrieved_documents: list[Document]
    relevant_documents: list[Document]
    retries: int
    answer: str


def llm() -> ChatOllama:
    return ChatOllama(model=settings.ollama_model, temperature=0)


def analyse_query(state: RAGState) -> RAGState:
    attempt = state.get("retries", 0) + 1
    prompt = "Rewrite this technical documentation question as a concise semantic-search query. Keep product names and error messages. This is retrieval attempt {attempt}; when attempt is greater than one, use different useful terms than the previous wording. Return only the rewritten query.\n\nQuestion: {question}".format(question=state["question"], attempt=attempt)
    return {"search_query": llm().invoke(prompt).content.strip(), "retries": state.get("retries", 0)}


def retrieve_documents(state: RAGState) -> RAGState:
    return {"retrieved_documents": get_vector_store().similarity_search(state["search_query"], k=settings.retrieval_k)}


def grade_documents(state: RAGState) -> RAGState:
    relevant: list[Document] = []
    for document in state.get("retrieved_documents", []):
        prompt = "Decide whether the document excerpt can help answer the question. Reply with exactly YES or NO. Be strict: a shared word alone is not enough.\n\nQuestion: {question}\nExcerpt: {excerpt}".format(question=state["question"], excerpt=document.page_content)
        if llm().invoke(prompt).content.strip().upper().startswith("YES"):
            relevant.append(document)
    return {"relevant_documents": relevant}


def generate_answer(state: RAGState) -> RAGState:
    context = "\n\n".join("[Source: {source}, chunk {chunk}]\n{text}".format(source=document.metadata["source_name"], chunk=document.metadata["chunk_index"], text=document.page_content) for document in state["relevant_documents"])
    prompt = "Answer only from the supplied technical-documentation context. If the context does not support a detail, say so plainly. End each factual paragraph with citations in the form [source name, chunk N]. Do not invent sources.\n\nQuestion: {question}\n\nContext:\n{context}".format(question=state["question"], context=context)
    return {"answer": llm().invoke(prompt).content.strip()}


def no_answer(_: RAGState) -> RAGState:
    return {"answer": "I don’t know based on the indexed documentation. Try a more specific question or ingest relevant documentation."}


def route_after_grading(state: RAGState) -> Literal["generate", "retry", "no_answer"]:
    if state.get("relevant_documents"):
        return "generate"
    return "retry" if state.get("retries", 0) < settings.max_retries else "no_answer"


def increment_retry(state: RAGState) -> RAGState:
    return {"retries": state.get("retries", 0) + 1}


def build_workflow():
    graph = StateGraph(RAGState)
    graph.add_node("analyse_query", analyse_query)
    graph.add_node("retrieve", retrieve_documents)
    graph.add_node("grade", grade_documents)
    graph.add_node("increment_retry", increment_retry)
    graph.add_node("generate", generate_answer)
    graph.add_node("no_answer", no_answer)
    graph.add_edge(START, "analyse_query")
    graph.add_edge("analyse_query", "retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grading, {"generate": "generate", "retry": "increment_retry", "no_answer": "no_answer"})
    graph.add_edge("increment_retry", "analyse_query")
    graph.add_edge("generate", END)
    graph.add_edge("no_answer", END)
    return graph.compile()


rag_workflow = build_workflow()
