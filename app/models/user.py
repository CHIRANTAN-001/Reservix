from sqlalchemy import (
    Boolean, 
    Text, 
    text, 
    String, 
    DateTime, 
    func,
    CHAR,
    UniqueConstraint,
    UUID
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import datetime

class User(Base):
    """
    User model
    Attributes:
        id: User ID
        name: User name
        phone: User phone number
        is_phone_verified: Whether the phone number is verified
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()"), # calls uuid_generate_v7() function to generate UUIDv7
    ) 
    
    name: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    country_code: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False
    )
    
    phone_number: Mapped[str] = mapped_column(
        String(15),
        nullable=False
    )    
    
    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('false')
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    
    # server_default → the DB sets this, not Python — avoids timezone issues
    created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True),
       server_default=func.now(),
       nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True),
       server_default=func.now(),
       onupdate=func.now(),
       nullable=False
    )

    

    __table_args__ = (
        UniqueConstraint("country_code", "phone_number", name="uq_country_phone"),
    )
    
    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name} code={self.country_code} phone={self.phone_number}>"