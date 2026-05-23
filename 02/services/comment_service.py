
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.comment import Comment, CommentLike


def create_comment(db: Session, post_id: int, content: str, author_id: str, parent_id: int = None) -> Comment:
    """댓글 또는 대댓글 작성"""
    # 게시글 존재 확인
    from models.post import Post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 대댓글인 경우 부모 댓글 존재 확인
    if parent_id is not None:
        parent_comment = db.query(Comment).filter(
            Comment.id == parent_id, Comment.post_id == post_id
        ).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="부모 댓글을 찾을 수 없습니다.")

    comment = Comment(
        post_id=post_id,
        parent_id=parent_id,
        content=content,
        author_id=author_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments(db: Session, post_id: int) -> List[Comment]:
    """특정 게시글의 최상위 댓글 목록 조회"""
    # 게시글 존재 확인
    from models.post import Post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 최상위 댓글만 조회 (parent_id가 None인 것)
    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .all()
    )
    return comments


def update_comment(db: Session, comment_id: int, content: str, author_id: str) -> Comment:
    """댓글 수정"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id != author_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 수정할 수 있습니다.")

    comment.content = content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int, author_id: str) -> dict:
    """댓글 삭제"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id != author_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 댓글만 삭제할 수 있습니다.")

    db.delete(comment)
    db.commit()
    return {"message": "댓글이 삭제되었습니다."}


def toggle_comment_like(db: Session, comment_id: int, user_id: str) -> dict:
    """댓글 좋아요 토글"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    existing_like = (
        db.query(CommentLike)
        .filter(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
        .first()
    )

    if existing_like:
        db.delete(existing_like)
        comment.likes_count = max(0, comment.likes_count - 1)
        db.commit()
        return {"message": "좋아요가 취소되었습니다.", "likes_count": comment.likes_count}
    else:
        new_like = CommentLike(comment_id=comment_id, user_id=user_id)
        db.add(new_like)
        comment.likes_count += 1
        db.commit()
        return {"message": "댓글을 좋아요했습니다.", "likes_count": comment.likes_count}
