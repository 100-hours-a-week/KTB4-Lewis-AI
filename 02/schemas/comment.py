
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


#요청 스키마

class CommentCreate(BaseModel):
    """댓글 작성 요청"""
    content: str = Field(..., min_length=1, description="댓글 내용")
    parent_id: Optional[int] = Field(None, description="대댓글인 경우 부모 댓글 ID")


class CommentUpdate(BaseModel):
    """댓글 수정 요청"""
    content: str = Field(..., min_length=1, description="수정할 댓글 내용")


# 응답 스키마

class CommentResponse(BaseModel):
    """댓글 응답 (대댓글 포함)"""
    id: int
    post_id: int
    parent_id: Optional[int]
    content: str
    author_id: str
    likes_count: int
    created_at: datetime
    updated_at: datetime
    is_toxic: Optional[bool] = None
    toxic_reason: Optional[str] = None
    replies: List["CommentResponse"] = []

    model_config = {"from_attributes": True}


# 자기참조 모델 업데이트
CommentResponse.model_rebuild()
