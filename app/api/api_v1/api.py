from fastapi import APIRouter

from app.api.endpoints import comments, friendships, likes, login, messages, posts, users

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
api_router.include_router(likes.router, prefix="/likes", tags=["likes"])
api_router.include_router(friendships.router, prefix="/friendships", tags=["friendships"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])