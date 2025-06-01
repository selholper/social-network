from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserBasic


# Shared properties
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


# Properties to receive via API on creation
class CommentCreate(CommentBase):
    post_id: int


# Properties to receive via API on update
class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


# Properties shared by models stored in DB
class CommentInDBBase(CommentBase):
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client
class Comment(CommentInDBBase):
    user: UserBasic
    like_count: Optional[int] = 0


# Properties stored in DB
class CommentInDB(CommentInDBBase):
    pass