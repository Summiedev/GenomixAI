"""Password hashing and signed access-token primitives.

This module intentionally uses the Python standard library so authentication does
not depend on a framework-specific JWT or password package. Passwords use PBKDF2
with a per-password random salt, and tokens are compact HMAC-SHA256 JWTs.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import Settings

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000


class TokenError(ValueError):
    """Raised when an access token is malformed, invalid, or expired."""


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(
        (
            PASSWORD_SCHEME,
            str(PASSWORD_ITERATIONS),
            _encode(salt),
            _encode(digest),
        )
    )


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        scheme, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        iterations = int(iterations_text)
        if scheme != PASSWORD_SCHEME or iterations < 100_000:
            return False
        salt = _decode(salt_text)
        expected = _decode(digest_text)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: UUID, settings: Settings) -> tuple[str, datetime, str]:
    _require_secret(settings)
    now = int(time.time())
    expires_at = datetime.fromtimestamp(now + settings.access_token_expire_minutes * 60, tz=UTC)
    jti = str(uuid4())
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    payload = {"sub": str(user_id), "iat": now, "exp": int(expires_at.timestamp()), "jti": jti}
    encoded_header = _encode_json(header)
    encoded_payload = _encode_json(payload)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return f"{encoded_header}.{encoded_payload}.{_encode(signature)}", expires_at, jti


def decode_access_token(token: str, settings: Settings) -> dict[str, object]:
    _require_secret(settings)
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_decode(encoded_header))
        payload = json.loads(_decode(encoded_payload))
        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise TokenError("Invalid token claims")
        if header.get("alg") != settings.jwt_algorithm or header.get("typ") != "JWT":
            raise TokenError("Invalid token header")
        supplied_signature = _decode(encoded_signature)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
        raise TokenError("Malformed token") from exc

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = hmac.new(
        settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise TokenError("Invalid token signature")
    subject = payload.get("sub")
    jti = payload.get("jti")
    expires = payload.get("exp")
    issued = payload.get("iat")
    if not isinstance(subject, str) or not isinstance(jti, str):
        raise TokenError("Missing token claims")
    if not isinstance(expires, int | float) or not isinstance(issued, int | float):
        raise TokenError("Invalid token timestamps")
    try:
        UUID(subject)
    except ValueError as exc:
        raise TokenError("Invalid token subject") from exc
    now = time.time()
    if expires <= now or issued > now + 60:
        raise TokenError("Expired or invalid token")
    return payload


def _require_secret(settings: Settings) -> None:
    if not settings.jwt_secret:
        raise TokenError("JWT secret is not configured")
    if settings.jwt_algorithm != "HS256":
        raise TokenError("Unsupported JWT algorithm")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _encode_json(value: dict[str, object]) -> str:
    return _encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


__all__ = [
    "TokenError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
