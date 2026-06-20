from collections.abc import Iterator

from app.generation.llm import generate_answer, stream_answer
from app.ingestion.loader import load_markdown_documents
from app.ingestion.splitter import split_document
from app.retrieval.vectorstore import query, upsert_chunks

TOP_K = 4


def ingest_all() -> int:
    """data/ 안의 모든 마크다운 문서를 청킹하여 Chroma에 적재하고, 적재된 청크 수를 반환한다."""
    total = 0
    for doc in load_markdown_documents():
        chunks = split_document(doc["source"], doc["text"])
        upsert_chunks(chunks)
        total += len(chunks)
    return total


def answer(question: str) -> tuple[str, list[dict]]:
    contexts = query(question, top_k=TOP_K)
    return generate_answer(question, contexts), contexts


def answer_stream(question: str) -> Iterator[str]:
    contexts = query(question, top_k=TOP_K)
    yield from stream_answer(question, contexts)
