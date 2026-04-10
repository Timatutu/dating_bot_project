import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.db.base import Base


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_likes_from_to"),
        Index("ix_likes_from_to", "from_user_id", "to_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(8), nullable=False)  # like / skip
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    from_user: Mapped["User"] = relationship(
        "User", back_populates="likes_sent", foreign_keys=[from_user_id]
    )
    to_user: Mapped["User"] = relationship(
        "User", back_populates="likes_received", foreign_keys=[to_user_id]
    )
