from app.core.database import Base
from sqlalchemy import text, Text, DateTime, func, ForeignKey, INTEGER, UUID
from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped


class Section(Base):
    __tablename__ = "section"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()"),
    )

    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    price: Mapped[int] = mapped_column(INTEGER, nullable=False)

    total_capacity: Mapped[int] = mapped_column(INTEGER, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Section id={self.id} name={self.name} event_id={self.event_id}>"
