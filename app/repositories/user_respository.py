from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import DuplicateColumnError, NoResultFound, IntegrityError

from app.models.user import User
from app.core.response import ConflictRequestError, NotFoundException

from typing import Optional, Mapping
from uuid import UUID

from app.schemas.user import UserUpdate
from app.schemas.otp import SendOTPBody

from app.core.utils import _build_update_clause

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_by_phone(self, payload: SendOTPBody) -> dict | None:
        result = await self.db.execute(
            select(
                User.id, 
                User.phone_number, 
                User.country_code, 
                User.name,
                User.is_phone_verified,
                
                User.created_at,
                User.updated_at
            )
            .where(User.country_code == payload.country_code)
            .where(User.phone_number == payload.phone_number)
        )
        row = result.mappings().one_or_none()
        
        if row is not None:
            return dict(row)
        else:
            return None
    
    async def create(
        self,
        payload: SendOTPBody,
    ) -> dict:
        query = text("""
            INSERT INTO users (
                country_code,
                phone_number,
                is_phone_verified
            )
            VALUES (
                :country_code,
                :phone_number,
                :is_phone_verified
            )
            ON CONFLICT (country_code, phone_number)
            DO UPDATE SET
                updated_at = NOW()
            RETURNING id, phone_number, country_code, name, is_phone_verified, created_at, updated_at;
        """)
        
        try:
            result = await self.db.execute(
                query,
                {
                    "country_code": payload.country_code,
                    "phone_number": payload.phone_number,
                    "is_phone_verified": True
                }
            )
            
            row = result.mappings().one()
            return dict(row)
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictRequestError("A user with this phone number already exists")
            raise
        
        
    async def update(
        self, 
        id: str,
        payload: UserUpdate
    ) -> dict:
        set_clause, bind_params = _build_update_clause(payload)
        
        query = text(f"""
            UPDATE users
            SET {set_clause}
            WHERE id = :id
            RETURNING id, name, email, created_at, updated_at, phone_number, country_code, is_phone_verified;
        """)
        
        try:
            result = await self.db.execute(
                query,
                {
                    "id": id,
                    **bind_params
                }
            )
            
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise
            
    async def get_user(
        self,
        id: str
    ) -> dict:
        query = text("""                     
            SELECT id, name, email, created_at, updated_at, phone_number, country_code, is_phone_verified
            FROM users
            WHERE id = :id;
        """)
        
        result = await self.db.execute(query, {"id": id})
        row = result.mappings().one()
        
        return dict(row)
        
        