from typing import List

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas as api_schemas
from ..db import get_db
from ..services import session_service


router = APIRouter()


def _get_current_user(db: Session, user_external_id: str | None) -> models.User:
    if not user_external_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user_id cookie")
    return session_service.get_or_create_user(db, user_external_id)


@router.get("/sessions", response_model=List[api_schemas.SessionOut])
def list_sessions(
    limit: int = 20,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    sessions = session_service.get_user_sessions(db, user, limit=limit)
    return sessions


@router.post("/sessions", response_model=api_schemas.SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: api_schemas.SessionCreate,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    session = session_service.create_session(db, user, title=payload.title, schema_id=payload.schema_id)
    return session


@router.patch("/sessions/{session_id}", response_model=api_schemas.SessionOut)
def update_session(
    session_id: int,
    payload: api_schemas.SessionUpdate,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    """Update a session's title or schema_id."""
    user = _get_current_user(db, user_external_id)
    sess = session_service.get_session(db, session_id, user)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if payload.title is not None:
        sess.title = payload.title
    if payload.schema_id is not None:
        sess.schema_id = payload.schema_id

    db.commit()
    db.refresh(sess)
    return sess


@router.get("/sessions/{session_id}/messages", response_model=List[api_schemas.MessageOut])
def list_messages(
    session_id: int,
    limit: int = 20,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    sess = session_service.get_session(db, session_id, user)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == sess.id)
        .order_by(models.Message.created_at.asc())
        .limit(limit)
        .all()
    )
    return messages


@router.post(
    "/sessions/{session_id}/messages",
    response_model=api_schemas.ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    session_id: int,
    payload: api_schemas.MessageCreate,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    """
    Core NL-to-SQL interaction endpoint.

    Model integration is implemented separately in model_service.generate_sql.
    """
    user = _get_current_user(db, user_external_id)
    sess = session_service.get_session(db, session_id, user)
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Block generation if no schema is attached
    if sess.schema is None or not sess.schema.raw_schema.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No schema attached to this session. Please select a schema from the dropdown before asking questions.",
        )

    # Store user message
    session_service.add_message(db, sess, role="user", content=payload.content)

    # Load active schema text (guaranteed to exist due to check above)
    schema_text = sess.schema.raw_schema

    # Lazy import to avoid circular dependency
    from ..services.model_service import generate_sql

    # Note: history_messages parameter kept for backward compatibility but not used
    # The orchestrator uses short prompts without history to avoid prompt poisoning
    sql, explanation, raw_output = generate_sql(
        nl_query=payload.content,
        schema_text=schema_text,
        history_messages=[],  # Not used by orchestrator, but kept for API compatibility
    )

    # Store assistant message
    assistant_content = sql if explanation is None else f"{sql}\n\n{explanation}"
    session_service.add_message(db, sess, role="assistant", content=assistant_content)

    return api_schemas.ChatResponse(sql=sql, explanation=explanation, raw_model_output=raw_output)

