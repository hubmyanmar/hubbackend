import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        DATABASE_URL = "sqlite:///./minutemind.db"
else:
    DATABASE_URL = DATABASE_URL or "sqlite:///./minutemind.db"

is_sqlite = DATABASE_URL.startswith("sqlite")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
