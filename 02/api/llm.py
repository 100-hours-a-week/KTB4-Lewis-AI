"""
LLM API 라우터 - Ollama 연동 엔드포인트
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from database import get_db
from services import llm_service

router = APIRouter(prefix="/llm", tags=["LLM (Ollama)"])


class ToxicCheckRequest(BaseModel):
    """악플 감지 요청"""
    content: str = Field(..., min_length=1, description="감지할 댓글 내용")


class ToxicCheckResponse(BaseModel):
    """악플 감지 응답"""
    is_toxic: bool
    analysis: str
    content: str


@router.post("/check-toxic", response_model=ToxicCheckResponse)
async def check_toxic_comment(request: ToxicCheckRequest):
    """
    댓글 내용이 악플인지 Ollama LLM으로 감지합니다.
    댓글 작성 전 사전 검사용으로 활용할 수 있습니다.
    """
    result = await llm_service.check_toxic(request.content)
    return ToxicCheckResponse(**result)
