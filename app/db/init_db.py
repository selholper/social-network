import logging
from sqlalchemy.orm import Session

from app.db.postgresql.base_class import Base
from app.db.postgresql.session import engine
from app.db.tarantool.connection import init_tarantool
from app.core.config import settings
from app.models import User

# Import all models to ensure they are registered with Base.metadata
from app.models import User, Post, Friendship, Comment, Like, Message

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database by creating all tables and setting up Tarantool spaces."""
    try:
        # Create all tables in PostgreSQL
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL tables created successfully")
        
        # Initialize Tarantool spaces and indexes
        init_tarantool()
        logger.info("Tarantool spaces initialized successfully")
        
        # Create initial users
        from app.db.postgresql.session import SessionLocal
        db = SessionLocal()
        try:
            create_initial_data(db)
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def create_initial_data(db: Session) -> None:
    """Create initial data in the database if needed."""
    # Check if we already have users
    user = db.query(User).first()
    if user:
        logger.info("Initial data already exists")
        return
    
    # Create a superuser
    superuser = User(
        username="admin",
        email="admin@example.com",
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        full_name="Admin User",
        is_superuser=True,
    )
    db.add(superuser)
    
    # Create a regular user
    regular_user = User(
        username="user",
        email="user@example.com",
        password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        full_name="Regular User",
    )
    db.add(regular_user)
    
    db.commit()
    logger.info("Initial data created successfully")