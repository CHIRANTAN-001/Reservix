from pydantic import  BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional, TypedDict
from uuid import UUID
import re

# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# --------------------------------------------------------------------

validate_phone_number_pattern = "^\\+?\\d{1,4}?[-.\\s]?\\(?\\d{1,3}?\\)?[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,9}$"

class UserGetByPhone(BaseModel):
    phone: str
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, phone: str):
        if not re.match(validate_phone_number_pattern, phone):
            raise ValueError("Invalid phone number")
        return phone
    

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

# ---------------------------------------------------------------------------
# Response schemas (what the API returns)
# ---------------------------------------------------------------------------

class TokenDict(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str

class UserCreateResponse(BaseModel):
    id: UUID
    name: Optional[str]
    country_code: str
    phone_number: str
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime
    token: TokenDict
    
    model_config = ConfigDict(from_attributes=True)
    
class UserResponse(BaseModel):
    id: UUID
    name: Optional[str]
    country_code: str
    phone_number: str
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime
    email: Optional[str]

class UserIdResponse(BaseModel):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)
