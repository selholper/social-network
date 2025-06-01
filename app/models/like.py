from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgresql.base_class import Base


class Like(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[Optional[int]] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"), index=True, nullable=True)
    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comment.id", ondelete="CASCADE"), index=True, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="likes")
    post: Mapped[Optional["Post"]] = relationship(
        "Post", 
        back_populates="likes",
        primaryjoin="and_(Like.post_id == Post.id, Like.comment_id == None)"
    )
    comment: Mapped[Optional["Comment"]] = relationship(
        "Comment", 
        back_populates="likes",
        primaryjoin="and_(Like.comment_id == Comment.id, Like.post_id == None)"
    )
    
    # Constraints
    __table_args__ = (
        # A user can like a post or comment only once
        UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
        UniqueConstraint('user_id', 'comment_id', name='unique_user_comment_like'),
        # A like must be associated with either a post or a comment, but not both
        CheckConstraint(
            "(post_id IS NULL AND comment_id IS NOT NULL) OR (post_id IS NOT NULL AND comment_id IS NULL)",
            name="check_like_target"
        ),
    )