"""
게시글(Post) 및 게시글 좋아요(PostLike) ORM 모델
"""

from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship

from database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    author_id = Column(String(100), nullable=False, index=True)  # UUID 형태의 익명 식별자
    views = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 관계 설정
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

    @property
    def comments_count(self) -> int:
        return len(self.comments)


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(100), nullable=False)

    # 한 유저가 같은 게시글에 중복 좋아요 방지
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_like"),)

    post = relationship("Post", back_populates="likes")
