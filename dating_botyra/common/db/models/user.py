import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sub_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="user", uselist=False, lazy="noload")
    rating: Mapped["Rating"] = relationship("Rating", back_populates="user", uselist=False, lazy="noload")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="user", lazy="noload")
    likes_sent: Mapped[list["Like"]] = relationship(
        "Like", back_populates="from_user", foreign_keys="Like.from_user_id", lazy="noload"
    )
    likes_received: Mapped[list["Like"]] = relationship(
        "Like", back_populates="to_user", foreign_keys="Like.to_user_id", lazy="noload"
    )
