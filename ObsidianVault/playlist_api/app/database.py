from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database file location
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./playlist.db")

# Create engine (check_same_thread=False is needed for SQLite in multithreaded environment like FastAPI)
engine = create_engine(
    DB_PATH, connect_args={"check_same_thread": False} if DB_PATH.startswith("sqlite") else {}
)

# Enable foreign keys for SQLite connections
if DB_PATH.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that yields a database session per request and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
