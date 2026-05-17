"""Data‑access objects (DAOs) for the persistence layer.

Each repository receives a SQLAlchemy ``Session`` (or ``AsyncSession`` in a
future async version) and provides simple CRUD methods that are used by the
application layer. Keeping the repositories thin makes them easy to mock in
unit tests.
"""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update

from .models import User, Transcription, TranscriptionMode, Conversation


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        self.session.flush()  # assign id
        return user

    def set_active(self, user_id: int, active: bool) -> None:
        self.session.execute(update(User).where(User.id == user_id).values(is_active=active))


class TranscriptionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, user_id: int, job_id: str, audio_filename: str, audio_path: Optional[str], mode: str, email: Optional[str] = None) -> Transcription:
        tr = Transcription(
            user_id=user_id,
            job_id=job_id,
            audio_filename=audio_filename,
            audio_path=audio_path,
            mode=mode,
            email=email,
        )
        self.session.add(tr)
        self.session.flush()
        return tr

    def get_by_job_id(self, job_id: str) -> Optional[Transcription]:
        return self.session.execute(select(Transcription).where(Transcription.job_id == job_id)).scalar_one_or_none()

    def get_by_filename_and_user(self, audio_filename: str, user_id: int) -> Optional[Transcription]:
        return self.session.execute(
            select(Transcription)
            .where(Transcription.audio_filename == audio_filename, Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
        ).scalar_one_or_none()

    def add_summary(self, job_id: str, mode: str, summary: str) -> None:
        """Add or replace a mode summary in the summaries JSON field."""
        tr = self.get_by_job_id(job_id)
        if not tr:
            return
        current = dict(tr.summaries or {})
        current[mode] = summary
        self.session.execute(
            update(Transcription).where(Transcription.job_id == job_id).values(summaries=current)
        )

    def list_by_user(self, user_id: int, offset: int = 0, limit: int = 20) -> List[Transcription]:
        stmt = (
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def update_status(self, job_id: str, status: str, **extra) -> None:
        data = {"status": status, "completed_at": datetime.utcnow()}
        data.update(extra)
        self.session.execute(update(Transcription).where(Transcription.job_id == job_id).values(**data))

    def delete(self, job_id: str) -> None:
        self.session.execute(delete(Transcription).where(Transcription.job_id == job_id))


class TranscriptionModeRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_or_update(self, transcription_id: int, mode: str, summary: str, status: str = "completed") -> TranscriptionMode:
        existing = self.session.execute(
            select(TranscriptionMode).where(
                TranscriptionMode.transcription_id == transcription_id,
                TranscriptionMode.mode == mode,
            )
        ).scalar_one_or_none()
        if existing:
            existing.summary = summary
            existing.status = status
            self.session.flush()
            return existing
        tm = TranscriptionMode(transcription_id=transcription_id, mode=mode, summary=summary, status=status)
        self.session.add(tm)
        self.session.flush()
        return tm

    def list_by_transcription(self, transcription_id: int) -> List[TranscriptionMode]:
        return self.session.execute(
            select(TranscriptionMode)
            .where(TranscriptionMode.transcription_id == transcription_id)
            .order_by(TranscriptionMode.created_at)
        ).scalars().all()

    def summaries_dict(self, transcription_id: int) -> dict:
        rows = self.list_by_transcription(transcription_id)
        return {r.mode: r.summary or "" for r in rows}


class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_message(self, transcription_id: int, role: str, content: str) -> Conversation:
        conv = Conversation(transcription_id=transcription_id, role=role, content=content)
        self.session.add(conv)
        self.session.flush()
        return conv

    def list_by_transcription(self, transcription_id: int) -> List[Conversation]:
        stmt = select(Conversation).where(Conversation.transcription_id == transcription_id).order_by(Conversation.timestamp)
        return self.session.execute(stmt).scalars().all()
