# Social Network Backend

A backend server for a social network application built with FastAPI, PostgreSQL, and Tarantool.

## Tech Stack

- **Web Framework**: FastAPI (Python)
- **Relational Database**: PostgreSQL (main data storage)
- **In-Memory Storage**: Tarantool (caching, sessions, high-load data)
- **Authentication**: JWT tokens

## Features

- User management (registration, authentication, profiles)
- Posts with text and image content
- Comments on posts
- Likes for posts and comments
- Friendship/follower relationships
- Direct messaging between users
- Caching of popular content and user feeds

## Project Structure

```
app/
├── api/                    # API endpoints
│   ├── api_v1/             # API version 1
│   │   └── api.py          # API router
│   ├── dependencies.py     # API dependencies
│   └── endpoints/          # API endpoint modules
│       ├── comments.py     # Comment endpoints
│       ├── friendships.py  # Friendship endpoints
│       ├── likes.py        # Like endpoints
│       ├── login.py        # Authentication endpoints
│       ├── messages.py     # Message endpoints
│       ├── posts.py        # Post endpoints
│       └── users.py        # User endpoints
├── core/                   # Core modules
│   ├── config.py           # Application configuration
│   └── security.py         # Security utilities
├── db/                     # Database modules
│   ├── init_db.py          # Database initialization
│   ├── postgresql/         # PostgreSQL modules
│   │   ├── base_class.py   # Base model class
│   │   └── session.py      # Database session
│   └── tarantool/          # Tarantool modules
│       └── connection.py   # Tarantool connection
├── models/                 # SQLAlchemy models
│   ├── comment.py          # Comment model
│   ├── friendship.py       # Friendship model
│   ├── like.py             # Like model
│   ├── message.py          # Message model
│   ├── post.py             # Post model
│   └── user.py             # User model
├── schemas/                # Pydantic schemas
│   ├── comment.py          # Comment schemas
│   ├── friendship.py       # Friendship schemas
│   ├── like.py             # Like schemas
│   ├── message.py          # Message schemas
│   ├── post.py             # Post schemas
│   ├── token.py            # Token schemas
│   └── user.py             # User schemas
└── main.py                 # Application entry point
```

## Entity Relationship Diagram

The database schema includes the following entities and relationships:

- **User**: Basic user information and authentication
  - Fields: id, username, email, password_hash, full_name, bio, avatar_url, is_active, is_superuser, created_at, updated_at
  
- **Post**: User-created content
  - Fields: id, user_id (FK), content, image_url, created_at, updated_at
  - Relationships: One user can have many posts

- **Comment**: Comments on posts
  - Fields: id, user_id (FK), post_id (FK), content, created_at, updated_at
  - Relationships: One post can have many comments, one user can create many comments

- **Like**: Likes on posts or comments
  - Fields: id, user_id (FK), post_id (FK|NULL), comment_id (FK|NULL), created_at
  - Relationships: A like can be associated with either a post or a comment (but not both)

- **Friendship**: Relationships between users
  - Fields: id, user_id (FK), friend_id (FK), status (pending/accepted/declined), created_at, updated_at
  - Relationships: Represents either one-way (follower) or two-way (friendship) relationships

- **Message**: Direct messages between users
  - Fields: id, sender_id (FK), recipient_id (FK), text, is_read, created_at, read_at
  - Relationships: One user can send many messages to another user

## Tarantool Usage

Tarantool is used for:

- Caching user sessions
- Storing and retrieving news feeds
- Caching popular posts
- Fast access to frequently accessed data

## Setup and Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure environment variables
6. Start the application: `uvicorn app.main:app --reload`

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

# Commands
`/opt/homebrew/opt/postgresql@17/bin/createuser -s postgres`