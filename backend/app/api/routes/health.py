from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request):
    try:
        async with request.app.state.session_factory() as s:
            await s.execute(text("select 1"))
        await request.app.state.redis.ping()
    except Exception:
        raise HTTPException(503, "dependency unavailable")
    return {"status": "ready"}
