from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.user import UserBasic


# Shared properties
class PostBase(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


# Properties to receive via API on creation
class PostCreate(PostBase):
    content: Optional[str] = Field(None, min_length=1)
    
    # Either content or image_url must be provided
    @validator('content', 'image_url')
    def check_content_or_image(cls, v, values):
        if not v and not values.get('image_url') and not values.get('content'):
            raise ValueError('Either content or image_url must be provided')
        return v
    
    class Config:
        from_attributes = True


# Properties to receive via API on update
class PostUpdate(PostBase):
    pass


# Properties shared by models stored in DB
class PostInDBBase(PostBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client
class Post(PostInDBBase):
    user: UserBasic
    like_count: Optional[int] = 0
    comment_count: Optional[int] = 0


# Properties stored in DB
class PostInDB(PostInDBBase):
    pass


# Post with minimal information for relationship display
class PostBasic(BaseModel):
    id: int
    user_id: int
    content: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True