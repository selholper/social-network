from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_tarantool
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.like import Like as LikeSchema, LikeCreate

router = APIRouter()


@router.post("/", response_model=LikeSchema)
def create_like(
    *,
    db: Session = Depends(get_db),
    like_in: LikeCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new like for a post or comment.
    """
    # Check if target exists
    if like_in.post_id is not None:
        target = db.query(Post).filter(Post.id == like_in.post_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if already liked
        existing_like = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.post_id == like_in.post_id,
            Like.comment_id == None
        ).first()
        
        if existing_like:
            raise HTTPException(status_code=400, detail="Post already liked")
        
        # Create like
        like = Like(
            user_id=current_user.id,
            post_id=like_in.post_id,
            comment_id=None
        )
        
        # Update post popularity in Tarantool
        try:
            tarantool = get_tarantool_connection()
            # Get current score
            result = tarantool.call(
                "box.space.popular_posts:get",
                [like_in.post_id]
            )
            
            if result:
                # Post exists in popular posts, update score
                current_score = result[0][1]
                tarantool.call(
                    "box.space.popular_posts:update",
                    [[like_in.post_id], [["=", 1, current_score + 1], ["=", 3, int(datetime.utcnow().timestamp())]]]
                )
            else:
                # Add post to popular posts
                post_data = db.query(Post).filter(Post.id == like_in.post_id).first()
                tarantool.call(
                    "box.space.popular_posts:insert",
                    [
                        like_in.post_id,
                        1,  # Initial score
                        {
                            "content": post_data.content or "",
                            "image_url": post_data.image_url or "",
                            "user_id": post_data.user_id,
                            "username": post_data.user.username
                        },
                        int(datetime.utcnow().timestamp())
                    ]
                )
            tarantool.close()
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error updating post popularity in Tarantool: {e}")
        
    elif like_in.comment_id is not None:
        target = db.query(Comment).filter(Comment.id == like_in.comment_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Check if already liked
        existing_like = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.comment_id == like_in.comment_id,
            Like.post_id == None
        ).first()
        
        if existing_like:
            raise HTTPException(status_code=400, detail="Comment already liked")
        
        # Create like
        like = Like(
            user_id=current_user.id,
            post_id=None,
            comment_id=like_in.comment_id
        )
    else:
        raise HTTPException(status_code=400, detail="Must specify either post_id or comment_id")
    
    db.add(like)
    db.commit()
    db.refresh(like)
    
    return like


@router.delete("/post/{post_id}", response_model=LikeSchema)
def delete_post_like(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove a like from a post.
    """
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id,
        Like.comment_id == None
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Update post popularity in Tarantool
    try:
        tarantool = get_tarantool_connection()
        # Get current score
        result = tarantool.call(
            "box.space.popular_posts:get",
            [post_id]
        )
        
        if result:
            # Post exists in popular posts, update score
            current_score = result[0][1]
            if current_score > 1:
                tarantool.call(
                    "box.space.popular_posts:update",
                    [[post_id], [["=", 1, current_score - 1], ["=", 3, int(datetime.utcnow().timestamp())]]]
                )
            else:
                # Remove post from popular posts if score would be 0
                tarantool.call(
                    "box.space.popular_posts:delete",
                    [post_id]
                )
        tarantool.close()
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error updating post popularity in Tarantool: {e}")
    
    db.delete(like)
    db.commit()
    
    return like


@router.delete("/comment/{comment_id}", response_model=LikeSchema)
def delete_comment_like(
    *,
    db: Session = Depends(get_db),
    comment_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Remove a like from a comment.
    """
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.comment_id == comment_id,
        Like.post_id == None
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    db.delete(like)
    db.commit()
    
    return like


@router.get("/post/{post_id}/liked", response_model=bool)
def check_post_liked(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Check if the current user has liked a post.
    """
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id,
        Like.comment_id == None
    ).first()
    
    return like is not None


@router.get("/comment/{comment_id}/liked", response_model=bool)
def check_comment_liked(
    *,
    db: Session = Depends(get_db),
    comment_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Check if the current user has liked a comment.
    """
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.comment_id == comment_id,
        Like.post_id == None
    ).first()
    
    return like is not None