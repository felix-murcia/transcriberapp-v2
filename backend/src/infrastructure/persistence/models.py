"""SQLAlchemy ORM models for the new persistent storage.

These replace the legacy IndexedDB storage. The models are deliberately
simple – they capture the data required by the business use‑cases and can be
extended later (e.g. adding indexes, relationships, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class User(Base):
    """Usuario del sistema.

    Sólo contiene los campos mínimos para autenticación; se pueden añadir
    atributos adicionales (nombre, avatar, etc.) según se necesite.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    transcriptions: Mapped[List["Transcription"]] = relationship(
        "Transcription", back_populates="user", cascade="all, delete-orphan"
    )


class Transcription(Base):
    """Registro de una transcripción de audio.

    Cada transcripción está asociada a un *User* y puede tener varias
    conversaciones (mensajes del agente) vinculadas.
    """

    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    audio_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_path: Mapped[Optional[str]] = mapped_column(String(1024))
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    transcription_text: Mapped[Optional[str]] = mapped_column(Text)
    summary_output: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relaciones
    user: Mapped[User] = relationship("User", back_populates="transcriptions")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="transcription", cascade="all, delete-orphan"
    )


class Conversation(Base):
    """Mensaje individual dentro de una conversación asociada a una transcripción.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcriptions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" o "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transcription: Mapped[Transcription] = relationship("Transcription", back_populates="conversations")
