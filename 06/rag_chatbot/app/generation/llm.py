from collections.abc import Iterator

from google import genai

from app.config import GEMINI_API_KEY, GEMINI_CHAT_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "당신은 카카오 테크 부트캠프 운영 규칙(출결, 공결 신청 등)을 안내하는 챗봇입니다. "
    "아래 제공된 [참고 문서]에 있는 내용만을 근거로 답변하세요. "
    "일상적인 대화나 표현등은 문서 외의 기존 지식을 활용하여 답변하세요"
)


def _build_prompt(question: str, contexts: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[{c['source']} - {c['heading'] or '본문'}]\n{c['text']}" for c in contexts
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"[참고 문서]\n{context_block}\n\n"
        f"[질문]\n{question}\n\n"
        f"[답변]"
    )


def generate_answer(question: str, contexts: list[dict]) -> str:
    prompt = _build_prompt(question, contexts)
    response = _client.models.generate_content(model=GEMINI_CHAT_MODEL, contents=prompt)
    return response.text


def stream_answer(question: str, contexts: list[dict]) -> Iterator[str]:
    prompt = _build_prompt(question, contexts)
    for chunk in _client.models.generate_content_stream(model=GEMINI_CHAT_MODEL, contents=prompt):
        if chunk.text:
            yield chunk.text
