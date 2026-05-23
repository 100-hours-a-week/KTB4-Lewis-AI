
import json
import httpx
from fastapi import HTTPException

from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def stream_summarize_text(content: str):
    """
    Ollama를 사용하여 게시글 내용을 요약하고 실시간으로 스트리밍합니다.
    """
    prompt = (
        "다음 게시글의 내용을 핵심만 간결하게 한국어 3줄로 요약해주세요.\n\n"
        f"게시글 내용:\n{content}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            result = json.loads(line)
                            token = result.get("response", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue

    except httpx.ConnectError:
        yield "Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요."
    except Exception as e:
        yield f"요약 스트리밍 중 오류 발생: {str(e)}"


async def check_toxic(content: str) -> dict:
    """
    Ollama를 사용하여 댓글이 악플인지 감지합니다.
    반환: {"is_toxic": bool, "reason": str, "confidence": str}
    """
    prompt = (
        "다음 댓글이 악플(욕설, 비하, 혐오, 인신공격 등)인지 판별해주세요.\n"
        "반드시 아래 형식으로만 답변해주세요:\n"
        "- 판별: [악플 / 정상]\n"
        "- 신뢰도: [높음 / 보통 / 낮음]\n"
        "- 사유: [간단한 이유]\n\n"
        f"댓글 내용: {content}"
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            result = response.json()
            llm_response = result.get("response", "")

            # 응답 파싱
            is_toxic = "악플" in llm_response and "정상" not in llm_response.split("판별")[0] if "판별" in llm_response else "악플" in llm_response
            return {
                "is_toxic": is_toxic,
                "analysis": llm_response.strip(),
                "content": content,
            }

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요.",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama 서버 응답 오류: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"악플 감지 처리 중 오류가 발생했습니다: {str(e)}",
        )
