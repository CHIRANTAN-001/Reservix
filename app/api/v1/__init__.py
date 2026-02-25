from fastapi import APIRouter
from app.api.v1.endpoints import users
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import event
from app.api.v1.endpoints import booking

# This is the v1 router — prefix /api/v1 is added in main.py
router = APIRouter()

router.include_router(users.router)
router.include_router(auth.router)
router.include_router(event.router)
router.include_router(booking.router)