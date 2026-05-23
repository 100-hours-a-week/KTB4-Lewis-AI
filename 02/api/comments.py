"""
댓글 API 라우터
"""

from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from core.security import get_anonymous_id
from schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from services import comment_service

router = APIRouter(tags=["댓글"])


async def check_toxic_in_background(comment_id: int):
    """댓글 작성 후 백그라운드에서 악플 여부를 판정하고 저장합니다."""
    from database import SessionLocal
    from models.comment import Comment
    from services import llm_service

    db = SessionLocal()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment:
            result = await llm_service.check_toxic(comment.content)
            comment.is_toxic = result.get("is_toxic", False)
            comment.toxic_reason = result.get("analysis", "")
            db.commit()
    except Exception as e:
        print(f"Error checking toxic in background: {e}")
    finally:
        db.close()


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """댓글 작성 (parent_id를 지정하면 대댓글)"""
    comment = comment_service.create_comment(
        db, post_id, comment_data.content, author_id, comment_data.parent_id
    )
    background_tasks.add_task(check_toxic_in_background, comment.id)
    return comment


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """특정 게시글의 댓글 목록 조회 (계층형 트리 구조)"""
    return comment_service.get_comments(db, post_id)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """댓글 수정 (본인 작성 댓글만 수정 가능)"""
    return comment_service.update_comment(db, comment_id, comment_data.content, author_id)


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    author_id: str = Depends(get_anonymous_id),
):
    """댓글 삭제 (본인 작성 댓글만 삭제 가능, 대댓글도 함께 삭제)"""
    return comment_service.delete_comment(db, comment_id, author_id)


@router.post("/comments/{comment_id}/like")
def toggle_comment_like(
    comment_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_anonymous_id),
):
    """댓글 좋아요 토글 (누르면 좋아요, 다시 누르면 취소)"""
    return comment_service.toggle_comment_like(db, comment_id, user_id)