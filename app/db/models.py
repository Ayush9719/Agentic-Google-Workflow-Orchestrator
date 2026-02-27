from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, TIMESTAMP
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), nullable=False, unique=True)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    intent = Column(JSONB, nullable=True)
    response = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class GmailCache(Base):
    __tablename__ = "gmail_cache"
    __table_args__ = (
        UniqueConstraint("user_id", "email_id", name="uq_gmail_user_email"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email_id = Column(String(255), nullable=False)
    subject = Column(Text, nullable=True)
    body_preview = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    received_at = Column(TIMESTAMP(timezone=True), nullable=True)


class GCalCache(Base):
    __tablename__ = "gcal_cache"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_gcal_user_event"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    start_time = Column(TIMESTAMP(timezone=True), nullable=True)


class GDriveCache(Base):
    __tablename__ = "gdrive_cache"
    __table_args__ = (
        UniqueConstraint("user_id", "file_id", name="uq_gdrive_user_file"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_id = Column(String(255), nullable=False)
    name = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)