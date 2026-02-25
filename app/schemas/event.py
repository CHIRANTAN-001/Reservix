from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# ---------------------------------------------------------------------------
class SectionCreate(BaseModel):
    name: str
    price: int = Field(gt=0)
    total_capacity: int = Field(gt=0)

class SectionInsert(SectionCreate):
    event_id: UUID

class EventCreate(BaseModel):
    name: str
    event_date: date
    sections: list[SectionCreate]
    
class EventInsert(BaseModel):
    owner_id: UUID
    name: str
    slug: str
    event_date: date
    
class SectionIdInsert(BaseModel):
    id: UUID
    sections: list[UUID]
    
# ---------------------------------------------------------------------------
# Response schemas (what the API returns)
# ---------------------------------------------------------------------------
    
class SectionResponse(BaseModel):
    id: UUID
    name: str
    price: int
    total_capacity: int

class EventCreateResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    slug: str
    sections: list[SectionResponse]
    
class SectionDetailsInfo(BaseModel):
    id: UUID
    name: str
    price: int
    total_capacity: int
    available_capacity: int
    is_sold_out: bool
    
    

class EventDetailsResponse(BaseModel):
    id :UUID
    name: str
    slug: str
    event_date: date
    sections: list[SectionDetailsInfo]