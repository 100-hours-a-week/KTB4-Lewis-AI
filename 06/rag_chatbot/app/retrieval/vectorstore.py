import chromadb

from app.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR
from app.retrieval.embedder import embed_query, embed_texts

_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
_collection = _client.get_or_create_collection(CHROMA_COLLECTION_NAME)


def upsert_chunks(chunks: list[dict]) -> None:
    """청크 {source, heading, text}들을 임베딩하여 Chroma에 upsert한다.

    id는 source+heading+순번 조합으로 만들어, 같은 문서를 재적재해도 중복되지 않는다.
    """
    if not chunks:
        return

    ids = [f"{c['source']}::{c['heading']}::{i}" for i, c in enumerate(chunks)]
    texts = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "heading": c["heading"] or ""} for c in chunks]
    embeddings = embed_texts(texts)

    _collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query(question: str, top_k: int = 4) -> list[dict]:
    """질문과 유사한 청크 top_k개를 {text, source, heading, distance} 형태로 반환한다."""
    query_embedding = embed_query(question)
    result = _collection.query(query_embeddings=[query_embedding], n_results=top_k)

    hits = []
    for text, metadata, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "source": metadata.get("source"),
                "heading": metadata.get("heading"),
                "distance": distance,
            }
        )
    return hits


def collection_count() -> int:
    return _collection.count()
