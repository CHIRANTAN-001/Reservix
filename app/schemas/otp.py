from pydantic import BaseModel
from uuid import UUID
from typing import Optional

# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# ---------------------------------------------------------------------------

class SendOTPBody(BaseModel):
    country_code: str
    phone_number: str

class SendOTPRequest(SendOTPBody):
    otp: str

# ---------------------------------------------------------------------------
# Response schemas (what the API returns)
# ---------------------------------------------------------------------------

class SendOTPResponse(BaseModel):
    id: UUID
    otp: str