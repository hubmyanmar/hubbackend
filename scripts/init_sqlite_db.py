"""Create all current SQLAlchemy tables in the SQLite DATABASE_URL from .env."""

from app.core.database import Base, DATABASE_URL, engine
import app.models  # noqa: F401  Load all mapped models before create_all.


def main() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        raise SystemExit("Refusing to initialize a non-SQLite DATABASE_URL")
    Base.metadata.create_all(bind=engine)
    print("SQLite schema initialized from the current SQLAlchemy models.")


if __name__ == "__main__":
    main()
