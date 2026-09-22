"""Minimal application authentication for the TYR internal workspace."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, Response

SESSION_COOKIE = "tyr_internal_session"
SESSION_MAX_AGE = int(os.getenv("TYR_SESSION_MAX_AGE_SECONDS", "28800"))
COOKIE_SECURE = os.getenv("TYR_AUTH_COOKIE_SECURE", "true").lower() == "true"
PBKDF2_ITERATIONS = 600_000
CSRF_HEADER = "X-CSRF-Token"


@dataclass(frozen=True)
class InternalSession:
    username: str
    role: str
    csrf_token: str
    expires_at: int


_login_failures: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required authentication configuration is missing: {name}")
    return value


def _auth_configured() -> bool:
    return all(os.getenv(name) for name in (
        "TYR_INTERNAL_USERNAME",
        "TYR_INTERNAL_PASSWORD_HASH",
        "TYR_INTERNAL_AUTH_SECRET",
    ))


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, 32)
    return "pbkdf2_sha256$" + str(iterations) + "$" + _b64(salt) + "$" + _b64(digest)


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 5_000_000:
            return False
        salt = _unb64(salt_text)
        expected = _unb64(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _sign(payload: bytes) -> str:
    secret = _required_env("TYR_INTERNAL_AUTH_SECRET").encode("utf-8")
    signature = hmac.new(secret, payload, hashlib.sha256).digest()
    return _b64(payload) + "." + _b64(signature)


def _verify(token: str) -> bytes | None:
    try:
        payload_text, signature_text = token.split(".", 1)
        payload = _unb64(payload_text)
        supplied = _unb64(signature_text)
        secret = _required_env("TYR_INTERNAL_AUTH_SECRET").encode("utf-8")
        expected = hmac.new(secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            return None
        return payload
    except (ValueError, TypeError, RuntimeError):
        return None


def create_session(username: str) -> str:
    now = int(time.time())
    payload = {
        "username": username,
        "role": "INTERNAL_OPERATOR",
        "csrf": secrets.token_urlsafe(32),
        "iat": now,
        "exp": now + SESSION_MAX_AGE,
    }
    return _sign(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def read_session(request: Request) -> InternalSession | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or not _auth_configured():
        return None
    payload = _verify(token)
    if payload is None:
        return None
    try:
        data = json.loads(payload)
        if int(data["exp"]) <= int(time.time()):
            return None
        if data["role"] != "INTERNAL_OPERATOR":
            return None
        if data["username"] != _required_env("TYR_INTERNAL_USERNAME"):
            return None
        return InternalSession(
            username=data["username"],
            role=data["role"],
            csrf_token=data["csrf"],
            expires_at=int(data["exp"]),
        )
    except (KeyError, TypeError, ValueError, RuntimeError):
        return None


def require_internal_operator(request: Request) -> InternalSession:
    session = read_session(request)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return session


def require_csrf(request: Request, session: InternalSession) -> None:
    supplied = request.headers.get(CSRF_HEADER)
    if not supplied or not hmac.compare_digest(supplied, session.csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def login(username: str, password: str) -> str:
    if not _auth_configured():
        raise RuntimeError("Authentication is not configured")
    now = time.monotonic()
    failures, retry_at = _login_failures[username]
    if retry_at > now:
        raise PermissionError("Authentication temporarily unavailable")
    configured_username = _required_env("TYR_INTERNAL_USERNAME")
    password_hash = _required_env("TYR_INTERNAL_PASSWORD_HASH")
    valid = hmac.compare_digest(username, configured_username) and verify_password(password, password_hash)
    if not valid:
        failures += 1
        delay = min(30.0, 2.0 ** min(failures - 1, 4))
        _login_failures[username] = (failures, now + delay)
        raise ValueError("Invalid credentials")
    _login_failures.pop(username, None)
    return create_session(configured_username)


def login_response(token: str) -> JSONResponse:
    response = JSONResponse({"authenticated": True, "role": "INTERNAL_OPERATOR"})
    set_session_cookie(response, token)
    return response


def login_page() -> Response:
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>TYR Intelligence Engine | Internal Login</title>
<link rel="stylesheet" href="/web/styles.css">
</head>
<body>
<header><a class="brand" href="/">TYR <span>INTELLIGENCE ENGINE</span></a></header>
<main>
<section class="workspace">
<div class="section-head">
<p class="eyebrow">INTERNAL ACCESS</p>
<h2>Authorized workspace</h2>
<p>Authentication is required to access deal records and internal processing.</p>
</div>
<form id="login-form" class="record">
<label>Username<input id="username" name="username" autocomplete="username" required></label>
<label>Password<input id="password" name="password" type="password" autocomplete="current-password" required></label>
<button class="primary" type="submit">SIGN IN</button>
<p id="login-error" class="error" aria-live="polite"></p>
</form>
</section>
</main>
<script>
const form = document.getElementById("login-form");
const error = document.getElementById("login-error");
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.textContent = "";
  const response = await fetch("/internal/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    credentials: "same-origin",
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value
    })
  });
  if (response.ok) {
    window.location.href = "/internal";
    return;
  }
  let message = "Authentication failed";
  try { message = (await response.json()).detail || message; } catch {}
  error.textContent = message;
});
</script>
</body>
</html>"""
    return Response(content=html, media_type="text/html")


def unauthorized_internal_redirect() -> RedirectResponse:
    return RedirectResponse(url="/internal/login", status_code=status.HTTP_303_SEE_OTHER)
