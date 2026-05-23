"""
게시글 API 라우터
"""

from typing import Optional, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from core.security import get_anonymous_id
from schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse
from services import post_service, llm_service

router = APIRouter(prefix="/posts", tags=["게시글"])


@router.post("/", response_model=PostResponse, status_code=201)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """게시글 작성"""
    return post_service.create_post(db, post_data, author_id)


@router.get("/", response_model=List[PostListResponse])
def get_posts(
    sort: str = "latest",
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    게시글 목록 조회
    - sort: latest(최신순), likes(추천순), views(조회순)
    - search: 제목/내용 검색 키워드
    - category: 카테고리 필터 (자유, 질문, 정보, 후기, 기술)
    """
    return post_service.get_posts(db, sort, search, category, skip, limit)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """게시글 상세 조회 (조회수 자동 증가)"""
    return post_service.get_post(db, post_id)


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """게시글 수정 (본인 작성 글만 수정 가능)"""
    return post_service.update_post(db, post_id, post_data, author_id)


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """게시글 삭제 (본인 작성 글만 삭제 가능)"""
    return post_service.delete_post(db, post_id, author_id)


@router.post("/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_anonymous_id),
):
    """게시글 추천 토글 (누르면 추천, 다시 누르면 취소)"""
    return post_service.toggle_post_like(db, post_id, user_id)


@router.post("/{post_id}/summarize")
async def summarize_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """게시글 내용을 Ollama LLM으로 요약하고 스트리밍합니다."""
    from models.post import Post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    generator = llm_service.stream_summarize_text(post.content)
    return StreamingResponse(generator, media_type="text/event-stream")
