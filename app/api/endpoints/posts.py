from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user, get_db, get_tarantool
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.post import Post as PostSchema, PostCreate, PostUpdate

router = APIRouter()


@router.get("/", response_model=List[PostSchema])
def read_posts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve posts.
    """
    # Get posts with user information and count likes and comments
    posts = (
        db.query(
            Post,
            func.count(func.distinct(Like.id)).label("like_count"),
            func.count(func.distinct(Comment.id)).label("comment_count")
        )
        .outerjoin(Like, (Like.post_id == Post.id) & (Like.comment_id == None))
        .outerjoin(Comment, Comment.post_id == Post.id)
        .group_by(Post.id)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert to schema format
    result = []
    for post, like_count, comment_count in posts:
        post_dict = PostSchema.from_orm(post).dict()
        post_dict["like_count"] = like_count
        post_dict["comment_count"] = comment_count
        result.append(PostSchema(**post_dict))
    
    return result


@router.post("/", response_model=PostSchema)
def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new post.
    """
    post = Post(
        user_id=current_user.id,
        content=post_in.content,
        image_url=post_in.image_url,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Add to Tarantool cache for news feed
    try:
        tarantool = get_tarantool_connection()
        # Add to user's followers' news feeds
        # This is a simplified example - in a real app, you'd get the user's followers
        # and add the post to their feeds
        tarantool.call(
            "box.space.news_feed_cache:insert",
            [current_user.id, post.id, int(post.created_at.timestamp()), {
                "content": post.content or "",
                "image_url": post.image_url or "",
                "user_id": current_user.id,
                "username": current_user.username
            }]
        )
        tarantool.close()
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error adding post to Tarantool cache: {e}")
    
    return post


@router.get("/{post_id}", response_model=PostSchema)
def read_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get post by ID.
    """
    post = (
        db.query(
            Post,
            func.count(func.distinct(Like.id)).label("like_count"),
            func.count(func.distinct(Comment.id)).label("comment_count")
        )
        .outerjoin(Like, (Like.post_id == Post.id) & (Like.comment_id == None))
        .outerjoin(Comment, Comment.post_id == Post.id)
        .filter(Post.id == post_id)
        .group_by(Post.id)
        .first()
    )
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_obj, like_count, comment_count = post
    post_dict = PostSchema.from_orm(post_obj).dict()
    post_dict["like_count"] = like_count
    post_dict["comment_count"] = comment_count
    
    return PostSchema(**post_dict)


@router.put("/{post_id}", response_model=PostSchema)
def update_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a post.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = post_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(post, field, update_data[field])
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Update in Tarantool cache
    try:
        tarantool = get_tarantool_connection()
        tarantool.call(
            "box.space.news_feed_cache:update",
            [[current_user.id, post.id], [
                ["=", 4, {
                    "content": post.content or "",
                    "image_url": post.image_url or "",
                    "user_id": current_user.id,
                    "username": current_user.username
                }]
            ]]
        )
        tarantool.close()
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error updating post in Tarantool cache: {e}")
    
    return post


@router.delete("/{post_id}", response_model=PostSchema)
def delete_post(
    *,
    db: Session = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a post.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete from Tarantool cache
    try:
        tarantool = get_tarantool_connection()
        tarantool.call(
            "box.space.news_feed_cache:delete",
            [current_user.id, post.id]
        )
        tarantool.close()
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error deleting post from Tarantool cache: {e}")
    
    db.delete(post)
    db.commit()
    
    return post


@router.get("/user/{user_id}", response_model=List[PostSchema])
def read_user_posts(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get posts by user ID.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get posts with user information and count likes and comments
    posts = (
        db.query(
            Post,
            func.count(func.distinct(Like.id)).label("like_count"),
            func.count(func.distinct(Comment.id)).label("comment_count")
        )
        .outerjoin(Like, (Like.post_id == Post.id) & (Like.comment_id == None))
        .outerjoin(Comment, Comment.post_id == Post.id)
        .filter(Post.user_id == user_id)
        .group_by(Post.id)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert to schema format
    result = []
    for post, like_count, comment_count in posts:
        post_dict = PostSchema.from_orm(post).dict()
        post_dict["like_count"] = like_count
        post_dict["comment_count"] = comment_count
        result.append(PostSchema(**post_dict))
    
    return result