from typing import List

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas as api_schemas
from ..db import get_db
from ..services.session_service import get_or_create_user


router = APIRouter()


def _get_current_user(db: Session, user_external_id: str | None) -> models.User:
    if not user_external_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user_id cookie")
    return get_or_create_user(db, user_external_id)


@router.get("/", response_model=List[api_schemas.SchemaOut])
def list_schemas(
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    return db.query(models.Schema).where(models.Schema.user_id == user.id).all()


@router.post("/", response_model=api_schemas.SchemaOut, status_code=status.HTTP_201_CREATED)
def create_schema(
    payload: api_schemas.SchemaCreate,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    schema = models.Schema(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        raw_schema=payload.raw_schema,
    )
    db.add(schema)
    db.commit()
    db.refresh(schema)
    return schema


@router.patch("/{schema_id}", response_model=api_schemas.SchemaOut)
def update_schema(
    schema_id: int,
    payload: api_schemas.SchemaUpdate,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    schema = (
        db.query(models.Schema)
        .filter(models.Schema.id == schema_id, models.Schema.user_id == user.id)
        .first()
    )
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    if payload.name is not None:
        schema.name = payload.name
    if payload.description is not None:
        schema.description = payload.description
    if payload.raw_schema is not None:
        schema.raw_schema = payload.raw_schema

    db.commit()
    db.refresh(schema)
    return schema


@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schema(
    schema_id: int,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db: Session = Depends(get_db),
):
    user = _get_current_user(db, user_external_id)
    schema = (
        db.query(models.Schema)
        .filter(models.Schema.id == schema_id, models.Schema.user_id == user.id)
        .first()
    )
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    db.delete(schema)
    db.commit()
    return None

