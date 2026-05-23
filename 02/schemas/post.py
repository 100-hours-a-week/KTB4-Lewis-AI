
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from core.config import CATEGORIES


# 요청 스키마

class PostCreate(BaseModel):
    """게시글 작성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")
    content: str = Field(..., min_length=1, description="게시글 내용")
    category: str = Field(..., description=f"카테고리 ({', '.join(CATEGORIES)})")

    def validate_category(self):
        if self.category not in CATEGORIES:
            raise ValueError(f"유효하지 않은 카테고리입니다. 선택 가능: {CATEGORIES}")
        return self


class PostUpdate(BaseModel):
    """게시글 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None


# 응답 스키마

class PostResponse(BaseModel):
    """게시글 응답"""
    id: int
    title: str
    content: str
    category: str
    author_id: str
    views: int
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    """게시글 목록 응답 (내용 미포함)"""
    id: int
    title: str
    category: str
    author_id: str
    views: int
    likes_count: int
    comments_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
