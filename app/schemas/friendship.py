from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.friendship import FriendshipStatus
from app.schemas.user import UserBasic


# Shared properties
class FriendshipBase(BaseModel):
    friend_id: int


# Properties to receive via API on creation
class FriendshipCreate(FriendshipBase):
    pass


# Properties to receive via API on update
class FriendshipUpdate(BaseModel):
    status: FriendshipStatus


# Properties shared by models stored in DB
class FriendshipInDBBase(FriendshipBase):
    id: int
    user_id: int
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client
class Friendship(FriendshipInDBBase):
    friend: UserBasic


# Properties stored in DB
class FriendshipInDB(FriendshipInDBBase):
    pass


# Friendship request with user information
class FriendRequest(BaseModel):
    id: int
    user: UserBasic
    status: FriendshipStatus
    created_at: datetime
    
    class Config:
        from_attributes = True