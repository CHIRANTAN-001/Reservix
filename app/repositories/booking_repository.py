from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.core.response import NotFoundException

from app.core.utils import _build_insert_clause, _build_update_clause
from app.schemas.booking import BookingCreateData, BookingConfirmRequest


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: BookingCreateData) -> dict:
        insert_clause, bind_params = _build_insert_clause(payload)

        query = text(f"""
            INSERT INTO bookings
            {insert_clause}
            RETURNING id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at, expires_at;             
        """)

        try:
            result = await self.db.execute(query, bind_params)
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise
    
    async def get_current_booking(self, user_id: str) -> dict | None:
        query = text("""
            SELECT id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at, expires_at
            FROM bookings
            WHERE user_id = :user_id
            AND status = 'HOLD'             
        """)
        
        try:
            result  = await self.db.execute(query, {"user_id": user_id})
            row = result.mappings().one_or_none()
            return dict(row) if row else None
        except NoResultFound:
            return None

    async def update(self, id: str, payload: BookingConfirmRequest) -> dict:
        set_clause, bind_params = _build_update_clause(payload)

        query = text(f"""
            UPDATE bookings
            SET {set_clause}
            WHERE id = :id
            AND status = 'HOLD'
            AND expires_at > EXTRACT(EPOCH FROM NOW())::BIGINT
            RETURNING id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at;              
        """)

        try:
            result = await self.db.execute(query, {"id": id, **bind_params})
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise
        except NoResultFound:
            await self.db.rollback()
            raise NotFoundException("Booking not found")

    async def get_confirm_by_id(self, id: str) -> dict | None:
        query = text("""
            SELECT id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at
            FROM bookings
            WHERE id = :id
            AND status = 'CONFIRMED';             
        """)

        result = await self.db.execute(query, {"id": id})
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def get_booking_by_id(self, id: str, user_id: str) -> dict | None:
        query = text("""
            SELECT 
                b.id as booking_id, 
                e.id as event_id, 
                e.name as event_name,
                e.slug as event_slug,
                e.event_date as event_date,
                s.id as section_id, 
                s.name as section_name,
                s.price as section_price,
                b.seats_requested,
                u.id as user_id,
                u.phone_number as user_phone_number,
                u.email as user_email,
                u.name as user_name,
                u.country_code as user_country_code,
                u.is_phone_verified as user_is_phone_verified,
                b.status, 
                b.created_at, 
                b.updated_at, 
                b.expires_at

            FROM bookings as b

            INNER JOIN events as e
                ON b.event_id = e.id
            INNER JOIN section as s
                ON b.section_id = s.id
            INNER JOIN users as u
                ON b.user_id = u.id 
            
            WHERE b.id = :id
            AND u.id = :user_id;             
        """)

        result = await self.db.execute(query, 
            {
                "id": id,
                "user_id": user_id
            }
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None
