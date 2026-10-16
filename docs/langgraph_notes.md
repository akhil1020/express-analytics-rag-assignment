# LangGraph workflow basics

LangGraph represents an application as a graph of named nodes operating on shared state. A `StateGraph` starts from a state schema, adds nodes and edges, then compiles the graph into an executable workflow.

Conditional edges select a next node from current state. They are useful when retrieval must follow a different path after grading evidence: relevant evidence can proceed to generation, while weak evidence can trigger another retrieval attempt.

Keeping the retry count in graph state prevents accidental infinite loops. A retrieval workflow should explicitly stop after a small number of retries and state that it lacks enough information when no relevant source is available.

Source: https://docs.langchain.com/oss/python/langgraph/overview
