from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    text
)
from app.schemas.otp import SendOTPRequest, SendOTPResponse
from sqlalchemy.exc import IntegrityError

from app.core.response import ConflictRequestError


from app.models.otp import OTP
from typing import Optional

class OTPRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def send_otp(self, data: SendOTPRequest) -> dict:
        query = text("""
            INSERT INTO otp (
                country_code,
                phone_number,
                otp
            )      
            VALUES (
                :country_code,
                :phone_number,
                :otp
            )       
            RETURNING id, otp;
        """)
        
        try:
            result = await self.db.execute(
                query,
                {
                    "country_code": data.country_code,
                    "phone_number": data.phone_number,
                    "otp": data.otp
                }
            )
            
            row = result.mappings().one()
            
            response = {
                "id":row["id"],
                "otp":row["otp"]
            }

            return response
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictRequestError("User already exists with this phone number")
            raise
        
    
    async def get_otp(self, data: SendOTPRequest) -> Optional[dict]:
        result = await self.db.execute(
            select(OTP.otp).where(OTP.country_code == data.country_code).where(OTP.phone_number == data.phone_number)
        )
        row = result.mappings().one_or_none()
        
        if row is not None:
            return {"otp": row["otp"]}
        else:
            return None