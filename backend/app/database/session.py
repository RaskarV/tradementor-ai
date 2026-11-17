from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

DATABASE_URL = get_settings().database_url
connect_args = {}
if DATABASE_URL.startswith(("postgresql", "postgresql+asyncpg")):
    # Required for Supabase's pgbouncer transaction pooler; SQLite cannot accept this argument.
    connect_args = {"statement_cache_size": 0}

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True, pool_size=5, max_overflow=5,
    connect_args=connect_args,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
