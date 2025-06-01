from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_tarantool
from app.models.message import Message
from app.models.user import User
from app.schemas.message import (
    Message as MessageSchema,
    MessageCreate,
    MessageUpdate,
    MessagePreview
)

router = APIRouter()


@router.post("/", response_model=MessageSchema)
def create_message(
    *,
    db: Session = Depends(get_db),
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new message.
    """
    # Check if recipient exists
    recipient = db.query(User).filter(User.id == message_in.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    # Check if trying to message self
    if message_in.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=message_in.recipient_id,
        text=message_in.text,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


@router.get("/", response_model=List[MessageSchema])
def read_messages(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve messages between current user and another user.
    """
    # Check if other user exists
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get messages between users
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Mark unread messages as read
    unread_messages = [
        msg for msg in messages 
        if msg.recipient_id == current_user.id and not msg.is_read
    ]
    
    if unread_messages:
        for msg in unread_messages:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
        
        db.add_all(unread_messages)
        db.commit()
    
    # Return in chronological order (oldest first)
    return sorted(messages, key=lambda x: x.created_at)


@router.get("/conversations", response_model=List[MessagePreview])
def read_conversations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a list of conversations (latest message from each user).
    """
    # This query gets the latest message from each conversation
    # It uses a subquery to find the max message ID for each user pair
    latest_message_ids = db.query(
        func.max(Message.id).label('max_id')
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id
        )
    ).group_by(
        func.least(Message.sender_id, Message.recipient_id),
        func.greatest(Message.sender_id, Message.recipient_id)
    ).subquery()
    
    # Get the actual messages using the IDs from the subquery
    latest_messages = db.query(Message).filter(
        Message.id.in_(db.query(latest_message_ids.c.max_id))
    ).order_by(Message.created_at.desc()).all()
    
    return latest_messages


@router.get("/unread", response_model=int)
def count_unread_messages(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Count unread messages for the current user.
    """
    count = db.query(func.count(Message.id)).filter(
        Message.recipient_id == current_user.id,
        Message.is_read == False
    ).scalar()
    
    return count


@router.put("/{message_id}", response_model=MessageSchema)
def update_message(
    *,
    db: Session = Depends(get_db),
    message_id: int,
    message_in: MessageUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Mark a message as read.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only the recipient can mark as read
    if message.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    message.is_read = message_in.is_read
    if message.is_read:
        message.read_at = datetime.utcnow()
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


@router.delete("/{message_id}", response_model=MessageSchema)
def delete_message(
    *,
    db: Session = Depends(get_db),
    message_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a message.
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender or recipient can delete
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(message)
    db.commit()
    
    return message