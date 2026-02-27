from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date

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


# Booking User Info
class BookingUserInfo(BaseModel):
    id: UUID
    name: Optional[str]
    country_code: str
    phone_number: str
    is_phone_verified: bool
    email: Optional[str]
# Booking Event Info
class BookingEventInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    event_date: date
# Booking Section Info
class BookingSectionInfo(BaseModel):
    id: UUID
    name: str
    price: int
    
class ConfirmBookingDetails(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    available_capacity: int
    user: BookingUserInfo
    event: BookingEventInfo
    section: BookingSectionInfo

# Booking Info
class BookingDetailsResponse(ConfirmBookingDetails):
    expires_at: int

    