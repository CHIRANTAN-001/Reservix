from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.redis import get_redis_client, Redis
from app.services.booking_service import BookingService

from app.core.utils import get_current_user
from app.core.response import created_response, success_response

from app.schemas.booking import BookingCreateRequest, BookingResponse, ConfirmBookingResponse, BookingDetailsResponse, ConfirmBookingDetails

router = APIRouter(
    prefix="/bookings",
    tags=["booking"],
)

def get_booking_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> BookingService:
    return BookingService(db, redis)


@router.post("/hold")
async def create_booking(
    payload: BookingCreateRequest,
    current_user_id: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
):
    booking: BookingResponse = await service.create_booking(user_id=current_user_id, payload=payload)
    return created_response(
        message="Booking created successfully",
        data=booking,
    )

@router.get("/current")
async def get_current_booking(
    current_user_id: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    booking: BookingResponse = await service.get_current_booking(user_id=current_user_id)
    return success_response(
        message="Booking retrieved successfully",
        data=booking
    )
    
@router.patch("/{id}/confirm")
async def confirm_booking(
    id: str,
    current_user_id: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    booking: ConfirmBookingResponse = await service.confirm_booking(id=id)
    return success_response(
        message="Booking confirmed successfully",
        data=booking
    )

@router.get('/{id}/ttl')
async def get_booking_by_id(
    id: str,
    current_user_id: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    booking: BookingDetailsResponse = await service.get_booking_by_id(
        id=id,
        user_id=current_user_id
    )
    return success_response(
        message="Booking retrieved successfully",
        data=booking
    )

@router.get('/{id}')
async def get_confirm_booking_by_id(
    id: str,
    current_user_id: str = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service)
):
    booking: ConfirmBookingDetails = await service.get_confirm_booking_by_id(
        id=id,
        user_id=current_user_id
    )
    return success_response(
        message="Booking retrieved successfully",
        data=booking
    )