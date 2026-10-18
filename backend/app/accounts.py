"""User accounts: sign up, sign in, sessions (HttpOnly cookie) and each user's saved bills.

Passwords are hashed with scrypt and a per-user salt; session tokens are random and only their
SHA-256 is stored, so a leaked database cannot be used to sign in.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from . import db
from .config import settings

COOKIE = "billsight_session"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter(prefix="/api")


# --------------------------------------------------------------------------- #
# Passwords and tokens
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
def start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = _now() + timedelta(days=settings.session_days)
    with db.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_now().isoformat(),))
        conn.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                     (_token_hash(token), user_id, expires.isoformat()))
    response.set_cookie(COOKIE, token, max_age=settings.session_days * 86400, httponly=True,
                        samesite="lax", secure=settings.secure_cookies, path="/")


def current_user(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    with db.connect() as conn:
        row = conn.execute(
            "SELECT u.id, u.name, u.email FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (_token_hash(token), _now().isoformat()),
        ).fetchone()
    return dict(row) if row else None


def require_user(request: Request) -> dict[str, Any]:
    user = current_user(request)
    if not user:
        raise HTTPException(401, "Please sign in to see your saved bills.")
    return user


# --------------------------------------------------------------------------- #
# Saved bills
# --------------------------------------------------------------------------- #
def save_bill(user_id: int, result: dict[str, Any]) -> int:
    bill = result["bill"]
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO bills (user_id, image_hash, bill_id, provider, bill_month, units, payable, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (user_id, image_hash) DO UPDATE SET
                 bill_id = excluded.bill_id, provider = excluded.provider, bill_month = excluded.bill_month,
                 units = excluded.units, payable = excluded.payable, data = excluded.data,
                 saved_at = datetime('now')""",
            (user_id, result["image_hash"], result["bill_id"], bill.get("provider"), bill.get("bill_month"),
             bill.get("units_consumed"), bill.get("payable_within_due_date"), json.dumps(result, ensure_ascii=False)),
        )
        row = conn.execute("SELECT id FROM bills WHERE user_id = ? AND image_hash = ?",
                           (user_id, result["image_hash"])).fetchone()
    return int(row["id"])


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #
class SignUp(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class SignIn(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


def _public(user: dict[str, Any]) -> dict[str, Any]:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.post("/auth/signup")
def signup(body: SignUp, response: Response) -> dict:
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Enter a valid email address.")
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Enter your name.")
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Sign in instead.")
        cur = conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                           (name, email, hash_password(body.password)))
        user_id = int(cur.lastrowid)
    start_session(response, user_id)
    return {"user": {"id": user_id, "name": name, "email": email}}


@router.post("/auth/login")
def login(body: SignIn, response: Response) -> dict:
    email = body.email.strip().lower()
    with db.connect() as conn:
        row = conn.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    start_session(response, int(row["id"]))
    return {"user": _public(dict(row))}


@router.post("/auth/logout")
def logout(request: Request, response: Response) -> dict:
    token = request.cookies.get(COOKIE)
    if token:
        with db.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request) -> dict:
    user = current_user(request)
    return {"user": _public(user) if user else None}


@router.get("/bills")
def list_bills(user: dict = Depends(require_user)) -> dict:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, bill_id, provider, bill_month, units, payable, saved_at FROM bills "
            "WHERE user_id = ? ORDER BY bill_month DESC, saved_at DESC",
            (user["id"],),
        ).fetchall()
    return {"bills": [dict(r) for r in rows]}


@router.get("/bills/{bill_pk}")
def get_bill(bill_pk: int, user: dict = Depends(require_user)) -> dict:
    with db.connect() as conn:
        row = conn.execute("SELECT data FROM bills WHERE id = ? AND user_id = ?", (bill_pk, user["id"])).fetchone()
    if not row:
        raise HTTPException(404, "This bill was not found in your account.")
    return json.loads(row["data"]) | {"saved_id": bill_pk}


@router.delete("/bills/{bill_pk}")
def delete_bill(bill_pk: int, user: dict = Depends(require_user)) -> dict:
    with db.connect() as conn:
        cur = conn.execute("DELETE FROM bills WHERE id = ? AND user_id = ?", (bill_pk, user["id"]))
    if not cur.rowcount:
        raise HTTPException(404, "This bill was not found in your account.")
    return {"ok": True}
