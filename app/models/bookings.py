from app.core.database import Base
from sqlalchemy import (
    UUID,
    INTEGER,
    Enum,
    func,
    DateTime,
    ForeignKey,
    CheckConstraint,
    text
)
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime

class BookingStatus(str, Enum):
    HOLD= "HOLD"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"

class Bookings(Base):
    __tablename__ = "bookings"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()")
    )
    
    user_id:Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False
    )
    
    section_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("section.id", ondelete="CASCADE"),
        nullable=False
    )
    
    seats_requested: Mapped[int] = mapped_column(
        INTEGER,
        nullable=False
    )
    
    status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus.HOLD,
            BookingStatus.CONFIRMED,
            BookingStatus.EXPIRED,
            name="booking_status"    
        ),
        nullable=False
    )
    
    expires_at:Mapped[int] = mapped_column(
        INTEGER,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    __table_args__ = (
        CheckConstraint("seats_requested > 0", name="check_seats_requested"),
    )
    
    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} event_id={self.event_id} section_id={self.section_id}>"