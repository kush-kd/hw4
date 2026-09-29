import hashlib
import secrets
from typing import Any

from database import get_connection

# Matches the scheme already used by the seed data's test user
# (pbkdf2_sha256$<salt>$<hex digest>, 120,000 iterations) so existing
# accounts and newly created ones can both be verified the same way.
PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, digest = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return secrets.compare_digest(candidate, digest)


def _is_valid_email(email: str) -> bool:
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and "." in domain and not domain.startswith(".")


def _public_user(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
    }


def create_user(first_name: str, last_name: str, email: str, password: str) -> dict[str, Any]:
    email = email.strip().lower()
    if not _is_valid_email(email):
        raise ValueError("Enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing is not None:
            raise ValueError("An account with that email already exists.")

        password_hash = hash_password(password)
        name = f"{first_name} {last_name}".strip()
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, first_name, last_name),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _public_user(row)
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return _public_user(row)
    finally:
        conn.close()
