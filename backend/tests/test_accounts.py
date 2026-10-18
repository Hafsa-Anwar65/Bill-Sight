from fastapi.testclient import TestClient

from app import accounts, extract
from tests.conftest import load


def client():
    from app.api import app

    return TestClient(app)


def signup(c, email="hafsa@example.com", password="secret123", name="Hafsa"):
    return c.post("/api/auth/signup", json={"name": name, "email": email, "password": password})


def test_password_hashing():
    h = accounts.hash_password("secret123")
    assert h.startswith("scrypt$") and "secret123" not in h
    assert accounts.verify_password("secret123", h)
    assert not accounts.verify_password("wrong", h)
    assert not accounts.verify_password("x", "garbage")


def test_signup_login_logout_flow():
    c = client()
    assert c.get("/api/auth/me").json() == {"user": None}

    r = signup(c)
    assert r.status_code == 200 and r.json()["user"]["email"] == "hafsa@example.com"
    assert c.get("/api/auth/me").json()["user"]["name"] == "Hafsa"

    assert signup(c).status_code == 409  # same email twice
    assert signup(client(), email="HAFSA@example.com").status_code == 409  # case-insensitive

    c.post("/api/auth/logout")
    assert c.get("/api/auth/me").json() == {"user": None}

    assert c.post("/api/auth/login", json={"email": "hafsa@example.com", "password": "nope"}).status_code == 401
    assert c.post("/api/auth/login", json={"email": "Hafsa@Example.com", "password": "secret123"}).status_code == 200
    assert c.get("/api/auth/me").json()["user"]["email"] == "hafsa@example.com"


def test_signup_validation():
    c = client()
    assert signup(c, email="not-an-email").status_code == 422
    assert signup(c, password="short").status_code == 422


def test_bills_are_saved_per_user(png_bytes, monkeypatch):
    monkeypatch.setattr(extract, "_gemini_reader", lambda p, d, m: load("ke_2026-09_159"))
    a, b = client(), client()
    signup(a)
    signup(b, email="saad@example.com", name="Saad")

    res = a.post("/api/analyze", files={"file": ("KESC_0002.png", png_bytes, "image/png")}).json()
    assert res["saved_id"]
    a.post("/api/analyze", files={"file": ("KESC_0002.png", png_bytes, "image/png")})  # same image: no duplicate

    mine = a.get("/api/bills").json()["bills"]
    assert len(mine) == 1 and mine[0]["payable"] == 7621 and mine[0]["bill_month"] == "2026-09"
    assert a.get(f"/api/bills/{mine[0]['id']}").json()["bill"]["provider"] == "KE"

    # another user cannot see or delete it
    assert b.get("/api/bills").json()["bills"] == []
    assert b.get(f"/api/bills/{mine[0]['id']}").status_code == 404
    assert b.delete(f"/api/bills/{mine[0]['id']}").status_code == 404

    assert a.delete(f"/api/bills/{mine[0]['id']}").json() == {"ok": True}
    assert a.get("/api/bills").json()["bills"] == []


def test_guest_can_still_analyze(png_bytes, monkeypatch):
    monkeypatch.setattr(extract, "_gemini_reader", lambda p, d, m: load("iesco_2026-09_58"))
    c = client()
    res = c.post("/api/analyze", files={"file": ("x.png", png_bytes, "image/png")})
    assert res.status_code == 200 and "saved_id" not in res.json()
    assert c.get("/api/bills").status_code == 401
