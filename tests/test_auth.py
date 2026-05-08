"""
Tests for the authentication endpoints:
  POST /auth/register
  POST /auth/login
  Role-based access control (admin vs member)
"""
import pytest
from fastapi.testclient import TestClient




# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def test_register_new_user(client: TestClient):
    """A new email registration should return 201 and a JWT token."""
    resp = client.post(
        "/auth/register",
        json={"email": "new_user@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient):
    """Registering the same email twice should return 400."""
    payload = {"email": "dupe@example.com", "password": "password1"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_default_role_is_member(client: TestClient):
    """Users registered without an explicit role should default to 'member'."""
    resp = client.post(
        "/auth/register",
        json={"email": "defaultrole@example.com", "password": "password"},
    )
    assert resp.status_code == 201
    # Decode token and verify by accessing a member-level endpoint
    token = resp.json()["access_token"]
    books_resp = client.get(
        "/books/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert books_resp.status_code == 200


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_valid_credentials(client: TestClient):
    """Valid credentials should return 200 and a JWT token."""
    email, password = "login_valid@example.com", "correct_password"
    client.post("/auth/register", json={"email": email, "password": password})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient):
    """Wrong password should return 401."""
    email = "wrongpass@example.com"
    client.post("/auth/register", json={"email": email, "password": "correct"})
    resp = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert resp.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Logging in with an unregistered email should return 401."""
    resp = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------

def test_admin_can_create_book(client: TestClient, admin_token: str):
    """Admin users should be able to POST /books/."""
    resp = client.post(
        "/books/",
        json={"title": "Admin Book", "author": "A", "isbn": "111-admin", "available_copies": 2},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201


def test_member_cannot_create_book(client: TestClient, member_token: str):
    """Member users should receive 403 when trying to POST /books/."""
    resp = client.post(
        "/books/",
        json={"title": "Member Book", "author": "B", "isbn": "222-member"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403


def test_unauthenticated_access_denied(client: TestClient):
    """Requests without a Bearer token should return 401."""
    resp = client.get("/books/")
    assert resp.status_code == 401


def test_expired_token_returns_401(client: TestClient):
    """A clearly invalid/expired token string should return 401."""
    resp = client.get(
        "/books/",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert resp.status_code == 401
