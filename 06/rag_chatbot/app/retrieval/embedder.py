from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """텍스트 리스트를 Gemini 임베딩 벡터 리스트로 변환한다."""
    response = _client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [embedding.values for embedding in response.embeddings]


def embed_query(query: str) -> list[float]:
    return embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
