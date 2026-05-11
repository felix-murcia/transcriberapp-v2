"""Persistence package – provides SQLAlchemy engine and session handling.

The project uses a classic synchronous SQLAlchemy session (compatible with the
existing synchronous FastAPI routes). For async usage the module could be
extended with ``AsyncSession``.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# La URL de la base de datos se leerá de la variable de entorno DATABASE_URL.
# Si no está definida, se usa una base SQLite local para desarrollo.
DATABASE_URL = Path(__file__).parent.parent.parent.parent / "dev.db"

engine = create_engine(
    f"sqlite:///{DATABASE_URL}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

def get_session() -> Session:
    """Factory used by FastAPI dependencies to obtain a DB session.

    Usage example::

        from fastapi import Depends
        from src.infrastructure.persistence import get_session

        def some_endpoint(db: Session = Depends(get_session)):
            ...
    """
    return SessionLocal()
