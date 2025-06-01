from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator


# Shared properties
class LikeBase(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    
    @validator('post_id', 'comment_id')
    def validate_target(cls, v, values, **kwargs):
        field = kwargs['field']
        if field.name == 'post_id' and v is not None and values.get('comment_id') is not None:
            raise ValueError('Cannot like both a post and a comment')
        if field.name == 'comment_id' and v is not None and values.get('post_id') is not None:
            raise ValueError('Cannot like both a post and a comment')
        if field.name == 'comment_id' and v is None and values.get('post_id') is None:
            raise ValueError('Must like either a post or a comment')
        return v


# Properties to receive via API on creation
class LikeCreate(LikeBase):
    pass


# Properties shared by models stored in DB
class LikeInDBBase(LikeBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client
class Like(LikeInDBBase):
    pass


# Properties stored in DB
class LikeInDB(LikeInDBBase):
    pass