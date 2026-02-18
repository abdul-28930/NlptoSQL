from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..services import auth_service


router = APIRouter()


class SignupPayload(BaseModel):
    email: EmailStr
    password: str


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupPayload, response: Response, db: Session = Depends(get_db)):
    user = auth_service.create_user(db, email=payload.email, password=payload.password)
    # Use email as external_id for now for compatibility with existing logic
    if not user.external_id:
        user.external_id = user.email
        db.add(user)
        db.commit()
        db.refresh(user)

    response.set_cookie(
        key="user_id",
        value=user.external_id,
        httponly=True,
        samesite="lax",
    )
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    external_id = user.external_id or user.email
    if user.external_id != external_id:
        user.external_id = external_id
        db.add(user)
        db.commit()
        db.refresh(user)

    response.set_cookie(
        key="user_id",
        value=external_id,
        httponly=True,
        samesite="lax",
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie("user_id")
    return None


@router.get("/me", response_model=UserOut)
def me(user_external_id: str | None = Cookie(default=None, alias="user_id"), db: Session = Depends(get_db)):
    if not user_external_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(models.User).filter(models.User.external_id == user_external_id).first()
    if not user or not user.email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

