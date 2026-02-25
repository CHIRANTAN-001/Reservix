from app.core.database import Base

from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime, date
from sqlalchemy import (
    Text,
    func,
    DateTime,
    text,
    ForeignKey,
    ARRAY,
    UUID,
    DATE
)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()"),
    )

    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)

    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    
    event_date: Mapped[date] = mapped_column(
        DATE,
        nullable=False
    )

    # Section id will have an array of foreign key to the section table
    sections: Mapped[list[str]] = mapped_column(
        ARRAY(
            UUID(as_uuid=False),
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name} slug={self.slug}>"
