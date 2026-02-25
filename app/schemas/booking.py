from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.bookings import BookingStatus

# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# ---------------------------------------------------------------------------
class BookingCreateRequest(BaseModel):
    event_id: UUID
    section_id: UUID
    seats_requested: int = Field(gt=0)


class BookingCreateData(BaseModel):
    event_id: UUID
    section_id: UUID
    seats_requested: int
    user_id: UUID
    status: str = BookingStatus.HOLD
    expires_at: int

class BookingConfirmRequest(BaseModel):
    status: str = BookingStatus.CONFIRMED
# ---------------------------------------------------------------------------
# Response schemas (what the API returns)
# ---------------------------------------------------------------------------
class SectionSeatInfo(BaseModel):
    available_capacity: int
class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    section_id: UUID
    seats_requested: int
    status: str
    created_at: datetime
    updated_at: datetime
    section: SectionSeatInfo
    expires_at: int

class ConfirmBookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    section_id: UUID
    seats_requested: int
    status: str
    created_at: datetime
    updated_at: datetime