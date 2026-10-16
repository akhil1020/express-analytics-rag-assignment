"""Index the small technical-documentation corpus incl"""

from pathlib import Path

from ingestion import make_documents
from store import index_documents


def main() -> None:
    for path in sorted(Path("docs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        document_id, documents = make_documents(text, path.name)
        index_documents(document_id, path.name, documents)
        print(f"Indexed {path.name} ({len(documents)} chunks)")


if __name__ == "__main__":
    main()
