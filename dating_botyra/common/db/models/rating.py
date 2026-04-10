import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.db.base import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (Index("ix_ratings_combined_score", "combined_score"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    primary_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    behavioral_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    combined_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="rating")
