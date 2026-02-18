from fastapi import Cookie, Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import get_db, init_db
from .models import generate_external_id
from .routes import auth, chat, schema


app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/users/bootstrap", tags=["users"])
def bootstrap_user(
    response: Response,
    user_external_id: str | None = Cookie(default=None, alias="user_id"),
    db=Depends(get_db),
):
    """
    Backwards-compatible bootstrap endpoint.

    For new flows, prefer explicit signup/login via /api/auth.
    """
    from .services.session_service import get_or_create_user

    if not user_external_id:
        user_external_id = generate_external_id()
        response.set_cookie(
            key="user_id",
            value=user_external_id,
            httponly=True,
            samesite="lax",
        )

    user = get_or_create_user(db, user_external_id)
    return {"user_id": user.id}


app.include_router(schema.router, prefix="/api/schemas", tags=["schemas"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

