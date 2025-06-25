"""
Database configuration and connection setup
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_DIR = Path(__file__).parent.parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/stock_analysis.db"

# Create engine with proper SQLite configuration
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "check_same_thread": False,  # Allow multiple threads for SQLite
    },
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables
    """
    # Import models to register them with Base
    from database.models import Stock, SelectionResult, ExecutionLog  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_URL}")
