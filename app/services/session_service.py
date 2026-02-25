from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.session_repository import SessionRepository
from app.services.otp_service import generate_access_token, settings

from app.core.response import NotFoundException

from app.schemas.session import AccessTokenResponse

class SessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.session_repo = SessionRepository(db)
        
    async def generate_access_token(self, token: str) -> AccessTokenResponse:
        session = await self.session_repo.get_by_token(token)

        if session is None:
            raise NotFoundException("Session not found")

        access_token = generate_access_token(
            sub=str(session["user_id"]),
            aud=session["phone_number"],
        )

        return AccessTokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        )
        