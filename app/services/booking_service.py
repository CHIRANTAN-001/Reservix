from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.booking_repository import BookingRepository
from app.repositories.section_inventory_repository import SectionInventoryRepository
from app.core.redis import Redis

from app.schemas.booking import (
    BookingCreateRequest, 
    BookingCreateData, 
    BookingResponse, 
    SectionSeatInfo,
    BookingConfirmRequest,
    BookingStatus,
    ConfirmBookingResponse
)
from uuid import UUID
from app.schemas.ttl import TTL

from datetime import datetime, timedelta
import time

from app.core.response import (
    NotFoundException,
    ConflictRequestError
)

def get_expires_at(ttl: int):
    now = datetime.now()
    expires_at = now + timedelta(seconds=ttl)
    return int(expires_at.timestamp())

class BookingService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.booking_repo = BookingRepository(db)
        self.section_inventory_repo = SectionInventoryRepository(db)

    async def create_booking(
        self, user_id: str, payload: BookingCreateRequest
    ) -> BookingResponse:
        # ---------------- Redis GET ----------------
        inventory_cache_key = f"section:{payload.event_id}:{payload.section_id}"
        inventory_cache = await self.redis.get(inventory_cache_key)

        if inventory_cache is None:
            raise NotFoundException("Section not found")

        if int(inventory_cache) < payload.seats_requested:
            raise ConflictRequestError("Not enough seats available")

        # ---------------- TTL Calculation ----------------
        expires_at = get_expires_at(int(TTL.TEN_MINUTES))

        # ---------------- DB INSERT ----------------
        booking_data = BookingCreateData(
            **payload.model_dump(), 
            user_id=UUID(user_id),
            expires_at=expires_at
        )

        result = await self.booking_repo.create(booking_data)

        if result is None:
            raise Exception("Failed to create booking")


        # ---------------- Redis Pipeline ----------------
        pipe = self.redis.pipeline()

        cache_key = f"booking:{result['id']}"

        pipe.setex(cache_key, int(TTL.TEN_MINUTES), result["seats_requested"])
        pipe.decr(inventory_cache_key, result["seats_requested"])
        pipe.get(inventory_cache_key)

        responses = await pipe.execute()

        available_capacity = int(responses[2])

        section_seat_info = {
            "available_capacity": available_capacity,
        }


        return BookingResponse(
            **result,
            expires_at=expires_at,
            section=SectionSeatInfo(**section_seat_info),
        )

    async def confirm_booking(self, id:str) -> ConfirmBookingResponse:
        async with self.db.begin():
            # check if confirm booking exists (implemented idempotency)
            confirm_booking = await self.booking_repo.get_confirm_by_id(id)
            if confirm_booking:
                return ConfirmBookingResponse(**confirm_booking)
            
            else:
                 # if not exists create
                payload = BookingConfirmRequest(
                    status=BookingStatus.CONFIRMED
                )
                # 1. update booking status
                update_booking_result = await self.booking_repo.update(id, payload)
                
                # 2. update section inventory
                await self.section_inventory_repo.update(
                    id=update_booking_result["section_id"],
                    payload={
                        "seats_requested": update_booking_result["seats_requested"]
                    }
                )
                # 3. delete cache
                cache_key = f"booking:{id}"
                
                await self.redis.delete(cache_key)
                # 4. return response
                return ConfirmBookingResponse(
                    **update_booking_result
                )