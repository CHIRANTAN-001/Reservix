from sqlalchemy import (
    CHAR,
    String,
    UniqueConstraint,
    text,
    DateTime,
    func,
    Text,
    UUID
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime

from app.core.database import Base

class OTP(Base):
    __tablename__ = "otp"
    
    id: Mapped[int] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()"),
    )
    country_code: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False
    )
    
    phone_number: Mapped[str] = mapped_column(
        String(15),
        nullable=False
    )
    
    otp: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="uq_otp_country_phone"),
    )
    
    def __repr__(self) -> str:
        return f"<OTP id={self.id} code={self.country_code} phone={self.phone_number}>"