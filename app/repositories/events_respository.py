from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.event import EventInsert, SectionIdInsert
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.response import ConflictRequestError

from app.core.utils import _build_insert_clause, _build_update_clause


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: EventInsert) -> dict:
        insert_clause, bind_params = _build_insert_clause(payload)

        query = text(f"""
            INSERT INTO events
            {insert_clause}
            RETURNING id, owner_id, name, slug, event_date, created_at, updated_at;
        """)

        try:
            result = await self.db.execute(query, bind_params)
            if result is None:
                await self.db.rollback()
                raise ConflictRequestError("Event with the same slug already exists")
            row = result.mappings().one()
            return dict(row)
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictRequestError("Event with the same slug already exists")
            raise

    async def update(self, payload: SectionIdInsert) -> dict:
        set_clause, bind_params = _build_update_clause(payload)

        query = text(f"""
            UPDATE events
            SET {set_clause}
            WHERE id = :id    
            RETURNING id, owner_id, name, slug, created_at, updated_at;         
        """)

        try:
            result = await self.db.execute(query, bind_params)
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise

    async def get_details_by_id(self, id: str) -> list[dict]:
        query = text("""
            SELECT 
                events.id as event_id, 
                events.name as event_name, 
                events.slug as event_slug, 
                events.event_date as event_date,
                section.id as section_id,
                section.name as section_name,
                section.price as section_price,
                section.total_capacity as section_total_capacity
            FROM events 
            JOIN section ON events.id = section.event_id
            WHERE events.id = :id
            FOR SHARE;
        """)
        
        result = await self.db.execute(query, {"id": id})
        rows = result.mappings().all()
        return [dict(row) for row in rows]
