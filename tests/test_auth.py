import hashlib
import os
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from app import auth
from app.main import app


def password_hash(password: str) -> str:
    salt = b"0123456789abcdef"
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000, 32)
    return "pbkdf2_sha256$600000$" + auth._b64(salt) + "$" + auth._b64(digest)


@pytest.fixture
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("ALETHEIA_DB_PATH", os.path.join(directory, "deals.db"))
        monkeypatch.setenv("TYR_INTERNAL_USERNAME", "operator")
        monkeypatch.setenv("TYR_INTERNAL_PASSWORD_HASH", password_hash("correct-password"))
        monkeypatch.setenv("TYR_INTERNAL_AUTH_SECRET", "test-only-secret-change-in-production")
        monkeypatch.setenv("TYR_AUTH_COOKIE_SECURE", "false")
        auth._login_failures.clear()
        yield TestClient(app)


def create_public_deal(client):
    response = client.post(
        "/api/deals",
        json={
            "name": "Security Test Deal",
            "asset_type": "Industrial",
            "location": "Dallas",
            "purchase_price": 10_000_000,
            "noi": 650_000,
        },
    )
    assert response.status_code == 200
    return response.json()


def login_client(client):
    response = client.post(
        "/internal/login",
        json={"username": "operator", "password": "correct-password"},
    )
    assert response.status_code == 200
    session = client.get("/api/internal/session")
    assert session.status_code == 200
    return session.json()["csrf_token"]


def test_public_routes_remain_public(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    create_public_deal(client)


def test_internal_workspace_requires_authentication(client):
    response = client.get("/internal", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/internal/login"


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/deals"),
        ("get", "/api/deals/not-authorized"),
        ("patch", "/api/deals/not-authorized/status"),
        ("get", "/api/deals/not-authorized/excel"),
    ],
)
def test_internal_api_requires_authentication(client, method, path):
    response = getattr(client, method)(
        path,
        json={"status": "HOLD"} if method == "patch" else None,
    )
    assert response.status_code == 401


def test_invalid_credentials_are_rejected(client):
    response = client.post(
        "/internal/login",
        json={"username": "operator", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_authenticated_operator_can_use_internal_workspace(client):
    deal = create_public_deal(client)
    csrf = login_client(client)

    assert client.get("/internal").status_code == 200
    assert client.get("/api/deals").status_code == 200
    assert client.get(f"/api/deals/{deal['deal_id']}").status_code == 200

    status_response = client.patch(
        f"/api/deals/{deal['deal_id']}/status",
        headers={"X-CSRF-Token": csrf},
        json={"status": "HOLD"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "HOLD"

    excel_response = client.get(f"/api/deals/{deal['deal_id']}/excel")
    assert excel_response.status_code == 200
    assert excel_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_status_mutation_requires_csrf(client):
    deal = create_public_deal(client)
    login_client(client)

    response = client.patch(
        f"/api/deals/{deal['deal_id']}/status",
        json={"status": "HOLD"},
    )
    assert response.status_code == 403


def test_logout_invalidates_session_cookie(client):
    login_client(client)
    assert client.get("/api/deals").status_code == 200
    assert client.post("/internal/logout").status_code == 204
    assert client.get("/api/deals").status_code == 401


def test_expired_session_is_rejected(client, monkeypatch):
    login_client(client)
    future = time.time() + auth.SESSION_MAX_AGE + 1
    monkeypatch.setattr(auth.time, "time", lambda: future)
    assert client.get("/api/deals").status_code == 401
