"""initial schema: pgvector extension, all tables, row level security

Baseline migration. It builds the schema from the models as they were at v1.0; every later change
must be a normal `alembic revision --autogenerate` migration so that history stays reproducible.
"""
from alembic import op

from app.database.base import Base
import app.database.models  # noqa: F401

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    # Supabase exposes tables through PostgREST. RLS with no policies denies the anon/authenticated roles;
    # the backend connects with the database owner role, which bypasses RLS.
    for table in Base.metadata.tables:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
