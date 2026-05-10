"""JWT helpers for Phase 4 tests."""
import os
from datetime import datetime, timedelta, timezone
import jwt  # PyJWT (server.py also imports `import jwt`)


def mint_expired_token(
    email: str = "expired@example.com",
    role: str = "viewer",
    ago_minutes: int = 5,
    secret: str | None = None,
    algorithm: str | None = None,
) -> str:
    """Forge a JWT whose `exp` is in the past (default 5 min ago).

    Uses JWT_SECRET from env if `secret` is None; falls back to the same
    hardcoded default that server.py:32 uses
    ('tenayan-fuel-management-secret-key-2024') so tests pass when
    JWT_SECRET is not exported.
    """
    secret = secret or os.environ.get(
        "JWT_SECRET", "tenayan-fuel-management-secret-key-2024"
    )
    algorithm = algorithm or os.environ.get("JWT_ALGORITHM", "HS256")
    payload = {
        "user_id": "expired-test-uuid",
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=ago_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)
