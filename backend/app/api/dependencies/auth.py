from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import decode_token, has_role
from app.config import get_settings
from app.database.models import AdminUser

_bearer = HTTPBearer(auto_error=False)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def current_admin(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                        db: AsyncSession = Depends(get_db)) -> AdminUser:
    if creds is None:
        raise HTTPException(401, "not authenticated")
    try:
        claims = decode_token(get_settings().jwt_secret, creds.credentials)
        admin = await db.get(AdminUser, int(claims["sub"]))
    except Exception:
        raise HTTPException(401, "invalid or expired token")
    if admin is None or not admin.is_active:
        raise HTTPException(401, "account disabled")
    return admin  # role comes from the database, not from the token, so demotions apply immediately


def require(minimum: str):
    async def dep(admin: AdminUser = Depends(current_admin)) -> AdminUser:
        if not has_role(admin.role.value, minimum):
            raise HTTPException(403, "insufficient role")
        return admin
    return dep
