from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# ---------------------------------------------------------------------------
# Request schemas (what the API accepts)
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    user_id: UUID
    token: str
    ipAddress: Optional[str]
    userAgent: Optional[str]



class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int