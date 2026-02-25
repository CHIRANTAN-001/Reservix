from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.section_inventory import SectionInventoryCreate
from app.core.utils import _build_insert_clause, _build_update_clause
from sqlalchemy.exc import IntegrityError
from app.core.response import ConflictRequestError

class SectionInventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create(
        self,
        payload: SectionInventoryCreate
    ) -> dict:
        set_clause, bind_params = _build_insert_clause(payload)
        query = text(f"""
            INSERT INTO section_inventory
            {set_clause}
            RETURNING section_id;
        """)
        
        try:
            result = await self.db.execute(query, bind_params)
            row = result.mappings().one()
            return dict(row)
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictRequestError("Section with the same id already exists")
            raise
    
    async def get_by_id(
        self,
        id: str
    ) -> dict:
        query = text("""
            SELECT section_id, total_capacity, available_capacity
            FROM section_inventory
            WHERE section_id = :id;
        """)
        
        result = await self.db.execute(query, {"id": id})
        row = result.mappings().one()
        return dict(row)
    
    async def update(
        self,
        id: str,
        payload
    ) -> dict:
        query = text("""
            UPDATE section_inventory
            SET 
                available_capacity = available_capacity - :seats_requested,
                version = version + 1,
                updated_at = NOW()
            WHERE section_id = :id
            AND available_capacity >= :seats_requested
            RETURNING section_id;           
        """)
        
        try:
            result = await self.db.execute(query, {
                "id": id,
                "seats_requested": payload["seats_requested"],
            })
            row = result.mappings().one()
            return dict(row)
        except IntegrityError:
            await self.db.rollback()
            raise
    