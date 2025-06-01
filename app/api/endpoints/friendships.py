from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
from app.schemas.friendship import (
    Friendship as FriendshipSchema,
    FriendshipCreate,
    FriendshipUpdate,
    FriendRequest
)
from app.schemas.user import UserBasic

router = APIRouter()


@router.post("/", response_model=FriendshipSchema)
def create_friendship_request(
    *,
    db: Session = Depends(get_db),
    friendship_in: FriendshipCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new friendship request.
    """
    # Check if friend exists
    friend = db.query(User).filter(User.id == friendship_in.friend_id).first()
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if trying to friend self
    if friendship_in.friend_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    # Check if friendship request already exists
    existing_request = db.query(Friendship).filter(
        Friendship.user_id == current_user.id,
        Friendship.friend_id == friendship_in.friend_id
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Friendship request already exists")
    
    # Check if reverse friendship request exists
    reverse_request = db.query(Friendship).filter(
        Friendship.user_id == friendship_in.friend_id,
        Friendship.friend_id == current_user.id
    ).first()
    
    if reverse_request:
        # Auto-accept if reverse request exists
        reverse_request.status = FriendshipStatus.ACCEPTED
        db.add(reverse_request)
        
        # Create new friendship with accepted status
        friendship = Friendship(
            user_id=current_user.id,
            friend_id=friendship_in.friend_id,
            status=FriendshipStatus.ACCEPTED
        )
    else:
        # Create new friendship request
        friendship = Friendship(
            user_id=current_user.id,
            friend_id=friendship_in.friend_id,
            status=FriendshipStatus.PENDING
        )
    
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    
    return friendship


@router.get("/", response_model=List[FriendshipSchema])
def read_friendships(
    *,
    db: Session = Depends(get_db),
    status: FriendshipStatus = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all friendships for the current user.
    """
    query = db.query(Friendship).filter(
        Friendship.user_id == current_user.id
    )
    
    if status:
        query = query.filter(Friendship.status == status)
    
    friendships = query.all()
    return friendships


@router.get("/requests", response_model=List[FriendRequest])
def read_friendship_requests(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve all pending friendship requests sent to the current user.
    """
    requests = db.query(Friendship).filter(
        Friendship.friend_id == current_user.id,
        Friendship.status == FriendshipStatus.PENDING
    ).all()
    
    return requests


@router.put("/{friendship_id}", response_model=FriendshipSchema)
def update_friendship(
    *,
    db: Session = Depends(get_db),
    friendship_id: int,
    friendship_in: FriendshipUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a friendship status (accept or decline).
    """
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    # Only the recipient can update the status
    if friendship.friend_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Only pending requests can be updated
    if friendship.status != FriendshipStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only update pending requests")
    
    friendship.status = friendship_in.status
    db.add(friendship)
    
    # If accepted, create reverse friendship
    if friendship_in.status == FriendshipStatus.ACCEPTED:
        # Check if reverse friendship already exists
        reverse_friendship = db.query(Friendship).filter(
            Friendship.user_id == friendship.friend_id,
            Friendship.friend_id == friendship.user_id
        ).first()
        
        if not reverse_friendship:
            reverse_friendship = Friendship(
                user_id=friendship.friend_id,
                friend_id=friendship.user_id,
                status=FriendshipStatus.ACCEPTED
            )
            db.add(reverse_friendship)
    
    db.commit()
    db.refresh(friendship)
    
    return friendship


@router.delete("/{friendship_id}", response_model=FriendshipSchema)
def delete_friendship(
    *,
    db: Session = Depends(get_db),
    friendship_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a friendship or friendship request.
    """
    friendship = db.query(Friendship).filter(Friendship.id == friendship_id).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    # Only the sender or recipient can delete
    if friendship.user_id != current_user.id and friendship.friend_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # If it's an accepted friendship, also delete the reverse friendship
    if friendship.status == FriendshipStatus.ACCEPTED:
        reverse_friendship = db.query(Friendship).filter(
            Friendship.user_id == friendship.friend_id,
            Friendship.friend_id == friendship.user_id
        ).first()
        
        if reverse_friendship:
            db.delete(reverse_friendship)
    
    db.delete(friendship)
    db.commit()
    
    return friendship


@router.get("/friends", response_model=List[UserBasic])
def read_friends(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all friends of the current user (accepted friendships).
    """
    friendships = db.query(Friendship).filter(
        Friendship.user_id == current_user.id,
        Friendship.status == FriendshipStatus.ACCEPTED
    ).all()
    
    friend_ids = [friendship.friend_id for friendship in friendships]
    friends = db.query(User).filter(User.id.in_(friend_ids)).all()
    
    return friends