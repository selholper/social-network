from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgresql.base_class import Base


class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    
    # Friendship relationships
    sent_friend_requests: Mapped[List["Friendship"]] = relationship(
        "Friendship", 
        foreign_keys="[Friendship.user_id]", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    received_friend_requests: Mapped[List["Friendship"]] = relationship(
        "Friendship", 
        foreign_keys="[Friendship.friend_id]", 
        back_populates="friend",
        cascade="all, delete-orphan"
    )
    
    # Message relationships
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", 
        foreign_keys="[Message.sender_id]", 
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_messages: Mapped[List["Message"]] = relationship(
        "Message", 
        foreign_keys="[Message.recipient_id]", 
        back_populates="recipient",
        cascade="all, delete-orphan"
    )