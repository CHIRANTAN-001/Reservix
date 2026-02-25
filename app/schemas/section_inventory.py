from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# ---------------------------------------------------------------------------
class SectionInventoryCreate(BaseModel):
    section_id: UUID
    total_capacity: int = Field(gt=0)
    available_capacity: int = Field(ge=0)
    