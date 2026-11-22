import hashlib
import hmac
import secrets
import json
import time
from typing import Any
from app.core.config import settings


def keyed_hash(value: str, purpose: str) -> str:
    """Computes a keyed HMAC-SHA256 hex digest for sensitive identifiers."""
    return hmac.new(
        settings.app_hmac_secret.encode(),
        f"{purpose}:{value}".encode(),
        hashlib.sha256
    ).hexdigest()


def hash_otp(otp: str, challenge_id: str) -> str:
    """Hashes an OTP together with its unique challenge ID."""
    return keyed_hash(f"{challenge_id}:{otp}", "otp")


def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def constant_time_equal(left: str, right: str) -> bool:
    """Timing-attack resistant string comparison."""
    return hmac.compare_digest(left, right)


def sign_callback_payload(payload_bytes: bytes, secret: str | None = None) -> str:
    """Generates an HMAC-SHA256 signature for provider webhook callbacks."""
    sec = secret or settings.mpesa_callback_secret
    return hmac.new(sec.encode(), payload_bytes, hashlib.sha256).hexdigest()


def verify_callback_signature(payload_bytes: bytes, signature: str, secret: str | None = None) -> bool:
    """Verifies provider webhook callback signature."""
    expected = sign_callback_payload(payload_bytes, secret)
    return constant_time_equal(expected, signature)


def create_mock_jwt(user_id: str, email: str = "user@nena.health", role: str = "authenticated", exp_seconds: int = 3600) -> str:
    """Creates a signed test JWT for mock/local tests."""
    from jose import jwt
    payload = {
        "sub": user_id,
        "id": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "exp": int(time.time()) + exp_seconds,
        "iat": int(time.time())
    }
    secret = settings.supabase_jwt_secret or settings.app_hmac_secret
    return jwt.encode(payload, secret, algorithm="HS256")
