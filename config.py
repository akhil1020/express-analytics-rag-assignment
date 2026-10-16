from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("data")
    collection_name: str = "technical_docs"
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    chunk_size: int = 1_000
    chunk_overlap: int = 200
    retrieval_k: int = 5
    max_retries: int = 2
    max_file_size_bytes: int = 10 * 1024 * 1024


settings = Settings()
