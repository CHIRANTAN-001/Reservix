from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.utils import _build_insert_clause

from app.schemas.event import SectionInsert

from app.core.response import ConflictRequestError

class SectionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create(self, payload:SectionInsert) -> dict:
        insert_clause, bind_params = _build_insert_clause(payload)
        query = text(f"""
            INSERT INTO section
            {insert_clause}
            RETURNING id, name, price, total_capacity;             
        """)
        try:
            result = await self.db.execute(query, bind_params)
            row = result.mappings().one()
            return dict(row)
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictRequestError("Section with the same name already exists")
            raise