"""Password hashing (scrypt) and JWT helpers. Secrets are passed in, never read from globals."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

import jwt

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "scrypt${}${}${}${}${}".format(_N, _R, _P, base64.b64encode(salt).decode(), base64.b64encode(dk).decode())


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, dk = stored.split("$")
        calc = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(calc, base64.b64decode(dk))
    except Exception:
        return False


def create_token(secret: str, admin_id: int, role: str, ttl_minutes: int = 480) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(admin_id), "role": role, "iat": now, "exp": now + ttl_minutes * 60},
                      secret, algorithm="HS256")


def decode_token(secret: str, token: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})


ROLE_RANK = {"educator": 1, "admin": 2, "owner": 3}


def has_role(role: str, minimum: str) -> bool:
    return ROLE_RANK.get(role, 0) >= ROLE_RANK[minimum]
