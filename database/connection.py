"""
Database Connection - PostgreSQL with SQLAlchemy Async
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment - defaults to SQLite for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./reelflow.db"
)

# For SQLite fallback during development (if PostgreSQL not available)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI endpoints.
    Yields database session and ensures cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Call this on application startup.
    """
    from . import models  # Import all models
    Base.metadata.create_all(bind=engine)
