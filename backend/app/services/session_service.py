from collections.abc import Sequence
from typing import Optional

from sqlalchemy.orm import Session

from .. import models

LAST_MESSAGES_LIMIT = 5


def get_or_create_user(db: Session, external_id: str) -> models.User:
    user = db.query(models.User).filter(models.User.external_id == external_id).first()
    if user:
        return user
    user = models.User(external_id=external_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(
    db: Session,
    user: models.User,
    title: str | None = None,
    schema_id: int | None = None,
) -> models.Session:
    session = models.Session(user_id=user.id, title=title, schema_id=schema_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, user: models.User, limit: int = 20) -> Sequence[models.Session]:
    return (
        db.query(models.Session)
        .filter(models.Session.user_id == user.id)
        .order_by(models.Session.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_session(db: Session, session_id: int, user: models.User) -> Optional[models.Session]:
    return (
        db.query(models.Session)
        .filter(models.Session.id == session_id, models.Session.user_id == user.id)
        .first()
    )


def get_last_messages(db: Session, session: models.Session, limit: int = LAST_MESSAGES_LIMIT) -> list[models.Message]:
    return (
        db.query(models.Message)
        .filter(models.Message.session_id == session.id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
        .all()[::-1]
    )


def add_message(db: Session, session: models.Session, role: str, content: str) -> models.Message:
    message = models.Message(session_id=session.id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

