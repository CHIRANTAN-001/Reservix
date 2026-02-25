from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.events_respository import EventRepository
from app.repositories.section_respository import SectionRepository
from app.repositories.section_inventory_repository import SectionInventoryRepository

from app.schemas.event import (
    EventCreate,
    EventCreateResponse,
    EventInsert,
    SectionInsert,
    SectionIdInsert,
    EventDetailsResponse,
    SectionDetailsInfo,
)
from app.schemas.section_inventory import SectionInventoryCreate

from app.core.response import NotFoundException

from uuid import UUID
from slugify import slugify
from app.core.redis import Redis

from datetime import datetime, date

import time


def calculate_ttl(event_date: date) -> int:
    event_date = datetime.strptime(str(event_date), "%Y-%m-%d")
    now = datetime.now()
    ttl = (event_date - now).total_seconds()
    return int(ttl)


class EventService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.event_repo = EventRepository(db)
        self.section_repo = SectionRepository(db)
        self.section_inventory_repo = SectionInventoryRepository(db)

    async def create_event(
        self, owner_id: str, payload: EventCreate
    ) -> EventCreateResponse:
        async with self.db.begin():
            # create event
            event = EventInsert(
                owner_id=UUID(owner_id),
                name=payload.name,
                slug=slugify(payload.name),
                event_date=payload.event_date,
            )
            event_row = await self.event_repo.create(event)

            # create sections
            created_sections = []
            for section in payload.sections:
                section_insert = SectionInsert(
                    event_id=event_row["id"],
                    name=section.name,
                    price=section.price,
                    total_capacity=section.total_capacity,
                )
                section_row = await self.section_repo.create(section_insert)
                created_sections.append(section_row)

            # update event
            sections_ids = [section["id"] for section in created_sections]
            event_update_payload = SectionIdInsert(
                id=event_row["id"], sections=sections_ids
            )
            event_update_row = await self.event_repo.update(event_update_payload)

            # create section inventory
            for section in created_sections:
                section_inventory_insert = SectionInventoryCreate(
                    section_id=section["id"],
                    total_capacity=section["total_capacity"],
                    available_capacity=section["total_capacity"],
                )
                await self.section_inventory_repo.create(section_inventory_insert)

            # write cache
            pipe = self.redis.pipeline()
            for section in created_sections:
                key = f"section:{event_row['id']}:{section['id']}"
                pipe.set(
                    key,
                    section["total_capacity"],
                    ex=calculate_ttl(event_row["event_date"]),
                )

            await pipe.execute()

            return EventCreateResponse(**event_update_row, sections=created_sections)

    async def get_event_details_by_id(self, id: str) -> EventDetailsResponse:
        cached_key = f"event:{id}"
        cached_event = await self.redis.get(cached_key)

        if cached_event is not None:
            return EventDetailsResponse.model_validate_json(cached_event)

        event_details = await self.event_repo.get_details_by_id(id)
        if not event_details:
            raise NotFoundException("Event not found")

        response = EventDetailsResponse(
            id=event_details[0]["event_id"],
            name=event_details[0]["event_name"],
            slug=event_details[0]["event_slug"],
            event_date=event_details[0]["event_date"],
            sections=[
                SectionDetailsInfo(
                    id=s["section_id"],
                    name=s["section_name"],
                    price=s["section_price"],
                    total_capacity=s["section_total_capacity"],
                    available_capacity=s["section_available_capacity"],
                    is_sold_out=s["is_sold_out"],
                )
                for s in event_details
            ],
        )

        await self.redis.setex(
            name=cached_key,
            value=response.model_dump_json(),
            time=calculate_ttl(event_details[0]["event_date"]),
        )

        return response
