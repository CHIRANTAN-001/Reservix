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
            RETURNING id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at;             
        """)

        try:
            result = await self.db.execute(query, bind_params)
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise

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
            result = await self.db.execute(query, {
                "id": id,
                **bind_params
            })
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise
        except NoResultFound:
            await self.db.rollback()
            raise NotFoundException("Booking not found")
        
    async def get_confirm_by_id(self, id:str) -> dict | None:
        query = text("""
            SELECT id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at
            FROM bookings
            WHERE id = :id
            AND status = 'CONFIRMED';             
        """)
        
        result = await self.db.execute(query, {"id": id})
        row = result.mappings().one_or_none()
        return dict(row) if row else None
