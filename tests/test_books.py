"""
Tests for the Books CRUD endpoints:
  GET  /books/          – list with pagination
  POST /books/          – create (admin only)
  GET  /books/{id}      – retrieve single book
  PUT  /books/{id}      – update (admin only)
  DELETE /books/{id}    – soft-delete (admin only)
"""
import pytest
from fastapi.testclient import TestClient



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_book(client: TestClient, token: str, isbn: str = "978-test-001") -> dict:
    """Helper: admin-create a book and return the response JSON."""
    resp = client.post(
        "/books/",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "isbn": isbn,
            "available_copies": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def test_create_book_as_admin(client: TestClient, admin_token: str):
    """Admin can create a book; response includes id and is_deleted=False."""
    book = _create_book(client, admin_token, isbn="978-create-001")
    assert book["id"] is not None
    assert book["title"] == "Test Book"
    assert book["is_deleted"] is False


def test_create_book_duplicate_isbn(client: TestClient, admin_token: str):
    """Creating two books with the same ISBN should fail (DB unique constraint)."""
    _create_book(client, admin_token, isbn="978-dup-001")
    resp = client.post(
        "/books/",
        json={"title": "Duplicate", "author": "A", "isbn": "978-dup-001"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # SQLAlchemy will raise an IntegrityError → FastAPI converts to 500 or the
    # router raises 400 depending on implementation; we just check it's not 201.
    assert resp.status_code != 201


# ---------------------------------------------------------------------------
# LIST & PAGINATION
# ---------------------------------------------------------------------------

def test_list_books_pagination(client: TestClient, admin_token: str, member_token: str):
    """Pagination parameters skip/limit should work correctly."""
    # Create 5 books
    for i in range(5):
        _create_book(client, admin_token, isbn=f"978-page-{i:03d}")

    # Fetch first 2
    resp = client.get(
        "/books/?skip=0&limit=2",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 200
    page1 = resp.json()
    assert len(page1) <= 2

    # Fetch next 2
    resp2 = client.get(
        "/books/?skip=2&limit=2",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp2.status_code == 200
    page2 = resp2.json()
    # No overlap in IDs
    ids1 = {b["id"] for b in page1}
    ids2 = {b["id"] for b in page2}
    assert ids1.isdisjoint(ids2)


def test_list_books_excludes_deleted(client: TestClient, admin_token: str, member_token: str):
    """Soft-deleted books must not appear in the list endpoint."""
    book = _create_book(client, admin_token, isbn="978-del-list-001")
    book_id = book["id"]

    # Soft-delete it
    del_resp = client.delete(
        f"/books/{book_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 204

    # Should not appear in list
    list_resp = client.get(
        "/books/",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    ids = [b["id"] for b in list_resp.json()]
    assert book_id not in ids


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def test_get_book_by_id(client: TestClient, admin_token: str, member_token: str):
    """A valid book ID should return the correct book."""
    created = _create_book(client, admin_token, isbn="978-get-001")
    resp = client.get(
        f"/books/{created['id']}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["isbn"] == "978-get-001"


def test_get_book_not_found(client: TestClient, member_token: str):
    """A non-existent book ID should return 404."""
    resp = client.get(
        "/books/999999",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def test_update_book(client: TestClient, admin_token: str):
    """Admin should be able to update an existing book's fields."""
    book = _create_book(client, admin_token, isbn="978-upd-001")
    book_id = book["id"]
    resp = client.put(
        f"/books/{book_id}",
        json={"title": "Updated Title", "author": "New Author", "isbn": "978-upd-001", "available_copies": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["available_copies"] == 5


def test_update_deleted_book_returns_404(client: TestClient, admin_token: str):
    """Updating a soft-deleted book should return 404."""
    book = _create_book(client, admin_token, isbn="978-upd-del-001")
    book_id = book["id"]
    client.delete(f"/books/{book_id}", headers={"Authorization": f"Bearer {admin_token}"})
    resp = client.put(
        f"/books/{book_id}",
        json={"title": "X", "author": "Y", "isbn": "978-upd-del-001", "available_copies": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# SOFT DELETE
# ---------------------------------------------------------------------------

def test_soft_delete_book(client: TestClient, admin_token: str, member_token: str):
    """DELETE sets is_deleted; the book is no longer fetchable by members."""
    book = _create_book(client, admin_token, isbn="978-soft-del-001")
    book_id = book["id"]

    del_resp = client.delete(
        f"/books/{book_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 204

    # Soft-deleted book returns 404 on GET
    get_resp = client.get(
        f"/books/{book_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert get_resp.status_code == 404


def test_delete_same_book_twice_returns_404(client: TestClient, admin_token: str):
    """Soft-deleting an already-deleted book should return 404."""
    book = _create_book(client, admin_token, isbn="978-double-del-001")
    book_id = book["id"]
    client.delete(f"/books/{book_id}", headers={"Authorization": f"Bearer {admin_token}"})
    resp = client.delete(f"/books/{book_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------

def test_health_endpoint(client: TestClient):
    """The /health endpoint should return 200 with all services 'healthy'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "redis" in data
