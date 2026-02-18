from datetime import datetime, timedelta, timezone
from typing import Optional

import hashlib
import hmac
import os

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import models


def _get_secret_key() -> bytes:
  """
  Very simple secret for password hashing.

  For a real production system, consider using passlib/bcrypt.
  """
  secret = os.getenv("AUTH_SECRET", "change-me-secret")
  return secret.encode("utf-8")


def _hash_password(password: str) -> str:
  secret = _get_secret_key()
  return hmac.new(secret, password.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
  return hmac.compare_digest(_hash_password(password), password_hash)


def create_user(db: Session, email: str, password: str) -> models.User:
  existing = db.query(models.User).filter(models.User.email == email).first()
  if existing:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User with this email already exists.",
    )

  user = models.User(
    email=email,
    password_hash=_hash_password(password),
  )
  db.add(user)
  db.commit()
  db.refresh(user)
  return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
  user = db.query(models.User).filter(models.User.email == email).first()
  if not user or not user.password_hash:
    return None
  if not verify_password(password, user.password_hash):
    return None
  return user

