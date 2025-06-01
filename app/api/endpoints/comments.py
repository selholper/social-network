from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import Comment as CommentSchema, CommentCreate, CommentUpdate

router = APIRouter()


@router.get("/post/{post_id}", response_model=List[CommentSchema])
def read_comments_by_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all comments for a post.
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get comments with like count
    comments = (
        db.query(
            Comment,
            func.count(Like.id).label("like_count")
        )
        .outerjoin(Like, (Like.comment_id == Comment.id) & (Like.post_id == None))
        .filter(Comment.post_id == post_id)
        .group_by(Comment.id)
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert to schema format
    result = []
    for comment, like_count in comments:
        comment_dict = CommentSchema.from_orm(comment).dict()
        comment_dict["like_count"] = like_count
        result.append(CommentSchema(**comment_dict))
    
    return result


@router.post("/", response_model=CommentSchema)
def create_comment(
    *,
    db: Session = Depends(get_db),
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new comment.
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == comment_in.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = Comment(
        user_id=current_user.id,
        post_id=comment_in.post_id,
        content=comment_in.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Add user information for response
    comment_dict = CommentSchema.from_orm(comment).dict()
    comment_dict["like_count"] = 0
    
    return CommentSchema(**comment_dict)


@router.get("/{comment_id}", response_model=CommentSchema)
def read_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a comment by ID.
    """
    comment = (
        db.query(
            Comment,
            func.count(Like.id).label("like_count")
        )
        .outerjoin(Like, (Like.comment_id == Comment.id) & (Like.post_id == None))
        .filter(Comment.id == comment_id)
        .group_by(Comment.id)
        .first()
    )
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment_obj, like_count = comment
    comment_dict = CommentSchema.from_orm(comment_obj).dict()
    comment_dict["like_count"] = like_count
    
    return CommentSchema(**comment_dict)


@router.put("/{comment_id}", response_model=CommentSchema)
def update_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a comment.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = comment_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(comment, field, update_data[field])
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Get like count for response
    like_count = (
        db.query(func.count(Like.id))
        .filter((Like.comment_id == comment.id) & (Like.post_id == None))
        .scalar()
    )
    
    comment_dict = CommentSchema.from_orm(comment).dict()
    comment_dict["like_count"] = like_count
    
    return CommentSchema(**comment_dict)


@router.delete("/{comment_id}", response_model=CommentSchema)
def delete_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a comment.
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(comment)
    db.commit()
    
    # For response format
    comment_dict = CommentSchema.from_orm(comment).dict()
    comment_dict["like_count"] = 0
    
    return CommentSchema(**comment_dict)