from app.core.database import Base
from sqlalchemy import DateTime, func, ForeignKey, CheckConstraint, UUID, INTEGER
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime


class SectionInventory(Base):
    __tablename__ = "section_inventory"

    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("section.id", ondelete="CASCADE"),
        primary_key=True,
    )

    total_capacity: Mapped[int] = mapped_column(INTEGER, nullable=False)

    available_capacity: Mapped[int] = mapped_column(
        INTEGER,
        nullable=False,
    )

    version: Mapped[int] = mapped_column(INTEGER, nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("available_capacity >= 0", name="check_available_capacity"),
    )
