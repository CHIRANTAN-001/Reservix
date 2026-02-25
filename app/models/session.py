from app.core.database import Base
from sqlalchemy import (
    Text,
    text,
    DateTime,
    func,
    UUID,
    ForeignKey
)
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime

class Session(Base):
    __tablename__ = "session"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("uuidv7()")
    )
    
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now() + text("INTERVAL '30 days'")
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
    
    ip_address: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    user_agent: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    # user = relationship("User", back_populates="sessions")