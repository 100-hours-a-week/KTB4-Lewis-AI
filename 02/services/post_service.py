"""
게시글 비즈니스 로직
"""

from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.post import Post, PostLike
from schemas.post import PostCreate, PostUpdate
from core.config import CATEGORIES


def create_post(db: Session, post_data: PostCreate, author_id: str) -> Post:
    """게시글 생성"""
    if post_data.category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 카테고리입니다. 선택 가능: {CATEGORIES}",
        )
    post = Post(
        title=post_data.title,
        content=post_data.content,
        category=post_data.category,
        author_id=author_id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_posts(
    db: Session,
    sort: str = "latest",
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Post]:
    """게시글 목록 조회 (정렬, 검색, 카테고리 필터)"""
    query = db.query(Post)

    # 카테고리 필터
    if category:
        query = query.filter(Post.category == category)

    # 제목/내용 검색
    if search:
        keyword = f"%{search}%"
        query = query.filter(
            (Post.title.like(keyword)) | (Post.content.like(keyword))
        )

    # 정렬
    if sort == "likes":
        query = query.order_by(Post.likes_count.desc(), Post.created_at.desc())
    elif sort == "views":
        query = query.order_by(Post.views.desc(), Post.created_at.desc())
    else:  # 기본: 최신순
        query = query.order_by(Post.created_at.desc())

    return query.offset(skip).limit(limit).all()


def get_post(db: Session, post_id: int) -> Post:
    """게시글 상세 조회 (조회수 +1)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 조회수 증가
    post.views += 1
    db.commit()
    db.refresh(post)
    return post


def update_post(db: Session, post_id: int, post_data: PostUpdate, author_id: str) -> Post:
    """게시글 수정 (작성자 검증)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != author_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 수정할 수 있습니다.")

    # 카테고리 유효성 검사
    if post_data.category is not None and post_data.category not in CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 카테고리입니다. 선택 가능: {CATEGORIES}",
        )

    # 전달된 필드만 업데이트
    update_fields = post_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: int, author_id: str) -> dict:
    """게시글 삭제 (작성자 검증)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != author_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시글만 삭제할 수 있습니다.")

    db.delete(post)
    db.commit()
    return {"message": "게시글이 삭제되었습니다."}


def toggle_post_like(db: Session, post_id: int, user_id: str) -> dict:
    """게시글 추천 토글 (이미 눌렀으면 취소, 아니면 추가)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    existing_like = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
        .first()
    )

    if existing_like:
        # 이미 추천했으면 취소
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        db.commit()
        return {"message": "추천이 취소되었습니다.", "likes_count": post.likes_count}
    else:
        # 추천 추가
        new_like = PostLike(post_id=post_id, user_id=user_id)
        db.add(new_like)
        post.likes_count += 1
        db.commit()
        return {"message": "게시글을 추천했습니다.", "likes_count": post.likes_count}
