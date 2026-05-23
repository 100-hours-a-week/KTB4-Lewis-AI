"""
댓글(Comment) 및 댓글 좋아요(CommentLike) ORM 모델
- 계층형 대댓글: parent_id를 통한 자기참조(self-referential) 관계
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)  # 대댓글용
    content = Column(Text, nullable=False)
    author_id = Column(String(100), nullable=False, index=True)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_toxic = Column(Boolean, nullable=True, default=None)
    toxic_reason = Column(Text, nullable=True)

    # 관계 설정
    post = relationship("Post", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")


class CommentLike(Base):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=False)

    # 한 유저가 같은 댓글에 중복 좋아요 방지
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_like"),)

    comment = relationship("Comment", back_populates="likes")
