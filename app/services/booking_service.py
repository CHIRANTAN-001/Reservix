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
    ConfirmBookingResponse,
    BookingUserInfo,
    BookingEventInfo,
    BookingSectionInfo,
    BookingDetailsResponse,
    ConfirmBookingDetails
)
from uuid import UUID
from app.schemas.ttl import TTL

from datetime import datetime, timedelta
import time

from app.core.response import NotFoundException, ConflictRequestError


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
            **payload.model_dump(), user_id=UUID(user_id), expires_at=expires_at
        )

        result = await self.booking_repo.create(booking_data)

        if result is None:
            raise Exception("Failed to create booking")

        # ---------------- Redis Pipeline ----------------
        pipe = self.redis.pipeline()

        cache_key = f"booking:{result['id']}"
        event_cache_key = f"event:{result['event_id']}"

        pipe.setex(cache_key, int(TTL.TEN_MINUTES), result["seats_requested"])
        pipe.decr(inventory_cache_key, result["seats_requested"])
        pipe.get(inventory_cache_key)
        pipe.delete(event_cache_key)

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

    async def confirm_booking(self, id: str) -> ConfirmBookingResponse:
        async with self.db.begin():
            # check if confirm booking exists (implemented idempotency)
            confirm_booking = await self.booking_repo.get_confirm_by_id(id)
            if confirm_booking:
                return ConfirmBookingResponse(**confirm_booking)

            else:
                # if not exists create
                payload = BookingConfirmRequest(status=BookingStatus.CONFIRMED)
                # 1. update booking status
                update_booking_result = await self.booking_repo.update(id, payload)

                # 2. update section inventory
                await self.section_inventory_repo.update(
                    id=update_booking_result["section_id"],
                    payload={
                        "seats_requested": update_booking_result["seats_requested"]
                    },
                )
                # 3. delete cache
                cache_key = f"booking:{id}"

                await self.redis.delete(cache_key)
                # 4. return response
                return ConfirmBookingResponse(**update_booking_result)

    async def get_booking_by_id(self, id: str, user_id: str) -> BookingDetailsResponse:
        result = await self.booking_repo.get_booking_by_id(id, user_id)
        if result is None:
            raise NotFoundException("Booking Not found")

        section_key = f"section:{result['event_id']}:{result['section_id']}"
        available_capacity = await self.redis.get(section_key)

        return BookingDetailsResponse(
            id=result["booking_id"],
            status=result["status"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            expires_at=result["expires_at"],
            available_capacity=available_capacity,
            user=BookingUserInfo.model_validate({
                "id": result["user_id"],
                "email": result["user_email"],
                "name": result["user_name"],
                "country_code": result["user_country_code"],
                "phone_number": result["user_phone_number"],
                "is_phone_verified": result["user_is_phone_verified"],   
            }),
            event=BookingEventInfo(
                id=result["event_id"],
                name=result["event_name"],
                slug=result["event_slug"],
                event_date=result["event_date"],
            ),
            section=BookingSectionInfo(
                id=result["section_id"],
                name=result["section_name"],
                price=result["section_price"],
            ),
        )
        
    async def get_confirm_booking_by_id(self, id: str, user_id: str) -> ConfirmBookingDetails:
        result = await self.booking_repo.get_booking_by_id(id, user_id)
        if result is None:
            raise NotFoundException("Booking Not found")

        section_key = f"section:{result['event_id']}:{result['section_id']}"
        available_capacity = await self.redis.get(section_key)

        return ConfirmBookingDetails(
            id=result["booking_id"],
            status=result["status"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            available_capacity=available_capacity,
            user=BookingUserInfo.model_validate({
                "id": result["user_id"],
                "email": result["user_email"],
                "name": result["user_name"],
                "country_code": result["user_country_code"],
                "phone_number": result["user_phone_number"],
                "is_phone_verified": result["user_is_phone_verified"],   
            }),
            event=BookingEventInfo(
                id=result["event_id"],
                name=result["event_name"],
                slug=result["event_slug"],
                event_date=result["event_date"],
            ),
            section=BookingSectionInfo(
                id=result["section_id"],
                name=result["section_name"],
                price=result["section_price"],
            ),
        )
