"""Create the first dashboard admin.  Usage (from backend/):
    python -m scripts.create_admin you@example.com --role owner --telegram-id 123456789"""
import argparse
import asyncio
import getpass

from sqlalchemy import select

from app.api.security import hash_password
from app.database.models import AdminRole, AdminUser
from app.database.session import SessionLocal


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("email")
    ap.add_argument("--role", choices=[r.value for r in AdminRole], default="owner")
    ap.add_argument("--telegram-id", type=int)
    a = ap.parse_args()
    pw = getpass.getpass("Password (min 12 chars): ")
    if len(pw) < 12 or pw != getpass.getpass("Repeat: "):
        raise SystemExit("Passwords differ or are shorter than 12 characters.")
    async with SessionLocal() as s:
        if await s.scalar(select(AdminUser.id).where(AdminUser.email == a.email.lower())):
            raise SystemExit("That email already exists.")
        s.add(AdminUser(email=a.email.lower(), password_hash=hash_password(pw), role=AdminRole(a.role),
                        telegram_id=a.telegram_id))
        await s.commit()
    print("Admin created.")


asyncio.run(main())
