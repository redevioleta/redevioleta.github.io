import os
from typing import Generator, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine

try:
    from core.config import settings
except ImportError:
    try:
        from core.config import settings
    except ImportError:
        settings = None

if settings is None:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
else:
    database_url = str(settings.database_url)

connect_args: dict[str, Any] = {"check_same_thread": False} if "sqlite" in database_url else {}
engine: Engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI para injetar uma sessão de banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
