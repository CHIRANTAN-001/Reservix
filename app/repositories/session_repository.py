from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.schemas.session import SessionCreate

class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def create(self, payload: SessionCreate) -> str:
        query = text("""
            INSERT INTO session(
                user_id,
                token,
                ip_address,
                user_agent
            )
            VALUES (
                :user_id,
                :token,
                :ip_address,
                :user_agent
            )
            RETURNING token;
        """)
        
        try:
            result = await self.db.execute(
                query,
                {
                    "user_id": payload.user_id,
                    "token": payload.token,
                    "ip_address": payload.ipAddress,
                    "user_agent": payload.userAgent
                }
            )
            
            row = result.mappings().one()
        
            return row["token"]
        except IntegrityError:
            await self.db.rollback()
            raise
    
    async def get_by_token(self, token: str) -> dict:
        query = text("""
            SELECT u.phone_number as phone_number, u.id as user_id
                FROM session as s
                LEFT JOIN users as u
                ON s.user_id = u.id
            WHERE s.token = :token
            AND expires_at > now();
        """)
        
        try:
            result = await self.db.execute(query, {"token": token})
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise