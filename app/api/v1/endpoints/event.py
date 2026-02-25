from  fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.database import get_db
from app.core.redis import get_redis_client,Redis
from app.services.event_service import EventService
from app.schemas.event import EventCreate, EventCreateResponse, EventDetailsResponse


from app.core.utils import get_current_user
from app.core.response import created_response, success_response

router = APIRouter(
    prefix="/events",
    tags=["event"],
)


def get_event_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client)
) -> EventService:
    return EventService(db, redis)

@router.post("/create")
async def create_event(
    payload: EventCreate,
    curent_user_id: str = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
):  
    print(payload.model_dump(mode="json"))
    event:EventCreateResponse = await service.create_event(
        owner_id = curent_user_id, 
        payload=payload
    )
    return created_response(
        message="Event created successfully",
        data=event
    )
    
@router.get("/{id}")
async def get_event_details_by_id(
    id: UUID,
    service: EventService = Depends(get_event_service)
):
    event_details:EventDetailsResponse = await service.get_event_details_by_id(str(id))
    return success_response(
        message="Event details retrieved successfully",
        data=event_details
    )