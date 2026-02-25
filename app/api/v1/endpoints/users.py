from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import (
    success_response,
    created_response,
)

from app.schemas.user import UserIdResponse, UserGetByPhone, UserUpdate, UserResponse
from app.services.user_service import UserService

from app.core.utils import get_current_user

router =APIRouter(
    prefix="/users",
    tags=["users"],
)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

def get_token(request: Request) -> str | None:
    return request.headers.get("Authorization")
    
@router.patch("/me")
async def update_user(
    payload: UserUpdate,
    current_user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    user: UserResponse = await service.update_user(current_user_id, payload)
    return success_response(
        message="User updated successfully",
        data=user,
    )

@router.get("/me")
async def get_user(
    current_user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    user: UserResponse = await service.get_user(current_user_id)
    return success_response(
        message="User retrieved successfully",
        data=user,
    )