from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserBasic


# Shared properties
class MessageBase(BaseModel):
    text: str = Field(..., min_length=1)


# Properties to receive via API on creation
class MessageCreate(MessageBase):
    recipient_id: int


# Properties to receive via API on update
class MessageUpdate(BaseModel):
    is_read: bool = True


# Properties shared by models stored in DB
class MessageInDBBase(MessageBase):
    id: int
    sender_id: int
    recipient_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Properties to return to client
class Message(MessageInDBBase):
    sender: UserBasic
    recipient: UserBasic


# Properties stored in DB
class MessageInDB(MessageInDBBase):
    pass


# Message with minimal information for chat preview
class MessagePreview(BaseModel):
    id: int
    sender_id: int
    text: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True