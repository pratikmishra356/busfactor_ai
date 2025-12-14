import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel


SESSION_DATA_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


class SessionExchangeInput(BaseModel):
    session_id: str


class UserOut(BaseModel):
    user_id: str
    email: str
    name: str
    picture: str | None = None
    # For localhost/dev where cookies may be blocked (cross-site), we optionally return the token
    # so the frontend can use Authorization: Bearer <token>.
    session_token: str | None = None


async def exchange_session(session_id: str):
    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.get(SESSION_DATA_URL, headers={"X-Session-ID": session_id})
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    return res.json()


async def upsert_user(db, *, email: str, name: str, picture: str | None):
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    now = datetime.now(timezone.utc)

    if existing:
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture, "updated_at": now.isoformat()}},
        )
        existing["name"] = name
        existing["picture"] = picture
        return existing

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.users.insert_one(doc)
    return doc


async def create_session(db, *, user_id: str, session_token: str):
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=7)

    await db.user_sessions.insert_one(
        {
            "user_id": user_id,
            "session_token": session_token,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
    )


async def get_user_from_session(db, session_token: str):
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        return None

    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at and expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        return None

    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    return user_doc


def get_session_token_from_request(request: Request) -> str | None:
    # Prefer cookie
    token = request.cookies.get("session_token")
    if token:
        return token

    # Fallback: Authorization header
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()

    return None


def set_session_cookie(
    response: Response,
    session_token: str,
    *,
    secure: bool,
    samesite: str,
):
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
        max_age=7 * 24 * 60 * 60,
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(key="session_token", path="/")
