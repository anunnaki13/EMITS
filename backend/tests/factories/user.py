"""Factory for user documents (Phase 4 D-02).

Creates users directly in the test DB with bcrypt-hashed passwords.
Use this for tests that need a custom user; existing tests continue to
use credentials from env vars.
"""
import os
import uuid
from datetime import datetime, timezone

import bcrypt
import pymongo


def _get_test_db_name() -> str:
    name = os.environ.get("MONGO_TEST_DB_NAME")
    if not name:
        raise RuntimeError(
            "MONGO_TEST_DB_NAME unset — factories must be called from inside a test session."
        )
    return name


def make_user(
    role: str = "admin",
    email: str | None = None,
    password: str = "testpassword123",
    **overrides,
) -> dict:
    """Insert one user document into the test DB. Returns doc dict (without _id).

    The password is bcrypt-hashed before insertion so /api/auth/login works against it.
    """
    if email is None:
        email = f"test-{uuid.uuid4().hex[:8]}@factory.test"

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password": hashed_password,
        "name": f"Test User ({role})",
        "role": role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "test-factory",
        **overrides,
    }
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
    try:
        mongo_client[_get_test_db_name()].users.insert_one(doc)
    finally:
        mongo_client.close()
    doc.pop("_id", None)
    # Return the cleartext password so callers can log in
    doc["_plaintext_password"] = password
    return doc
