import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (BigInteger, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer,
                        JSON, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database.base import Base, TimestampMixin

EMB_DIM = get_settings().embedding_dim


class Experience(str, enum.Enum):
    complete_beginner = "complete_beginner"
    beginner = "beginner"
    intermediate = "intermediate"
    experienced = "experienced"


class Decision(str, enum.Enum):
    cleared = "cleared"
    blocked = "blocked"


class TicketStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    answered = "answered"
    closed = "closed"


class AdminRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    educator = "educator"


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False,
                                                  cascade="all, delete-orphan", lazy="joined")


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    has_traded: Mapped[bool | None] = mapped_column(Boolean)
    experience: Mapped[Experience | None] = mapped_column(Enum(Experience, name="experience"))
    learning_capital: Mapped[float | None] = mapped_column(Numeric(14, 2))
    objectives: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(32), default="English", server_default="English")
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    user: Mapped[User] = relationship(back_populates="profile")
    __table_args__ = (CheckConstraint("learning_capital IS NULL OR learning_capital >= 0",
                                      name="ck_profile_capital_nonneg"),)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    summary: Mapped[str | None] = mapped_column(Text)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)                      # exactly what was delivered / received
    original_draft: Mapped[str | None] = mapped_column(Text)        # only set when the gate blocked a draft
    compliance_decision: Mapped[str | None] = mapped_column(String(16))
    compliance_rules: Mapped[list | None] = mapped_column(JSON)
    telegram_update_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    __table_args__ = (CheckConstraint("role in ('user','assistant','admin','system')", name="ck_message_role"),)


class ComplianceLog(Base):
    __tablename__ = "compliance_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"))
    decision: Mapped[Decision] = mapped_column(Enum(Decision, name="decision"), index=True)
    matched_rules: Mapped[list] = mapped_column(JSON, default=list)
    severity: Mapped[str | None] = mapped_column(String(16), index=True)
    excerpt: Mapped[str | None] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(32), default="reply")
    used_safe_alternative: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ComplianceRule(Base, TimestampMixin):
    __tablename__ = "compliance_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    category: Mapped[str] = mapped_column(String(64))
    pattern: Mapped[str | None] = mapped_column(Text)               # custom rules only
    severity: Mapped[str] = mapped_column(String(16), default="HIGH")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    __table_args__ = (CheckConstraint("severity in ('LOW','MEDIUM','HIGH','CRITICAL')", name="ck_rule_severity"),)


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole, name="admin_role"), default=AdminRole.educator)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class SupportRequest(Base, TimestampMixin):
    __tablename__ = "support_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_code: Mapped[str] = mapped_column(String(16), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"))
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"), index=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus, name="ticket_status"),
                                                 default=TicketStatus.pending, index=True)
    context_snapshot: Mapped[str | None] = mapped_column(Text)


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str | None] = mapped_column(String(512))
    body: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(cascade="all, delete-orphan", passive_deletes=True)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMB_DIM))
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_idx"),
                      Index("ix_chunk_embedding", "embedding", postgresql_using="hnsw",
                            postgresql_ops={"embedding": "vector_cosine_ops"}))


class BotSetting(Base, TimestampMixin):
    __tablename__ = "bot_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)  # never store secrets here


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    target: Mapped[str | None] = mapped_column(String(128))
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
