from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_respository import UserRepository

from app.core.response import NotFoundException, ConflictRequestError

from app.schemas.user import UserResponse, UserUpdate

class UserService:
    
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        
    async def update_user(
        self,
        id: str,
        payload: UserUpdate
    )-> UserResponse:
        result = await self.repo.update(id, payload)
        
        if result is None:
            raise NotFoundException("User not found")
        print(UserResponse.model_validate(result))
        return UserResponse.model_validate(result)
    
    async def get_user(
        self,
        id: str
    ) -> UserResponse:
        result = await self.repo.get_user(id)
        if result is None:
            raise NotFoundException("User not found")
        return UserResponse.model_validate(result)