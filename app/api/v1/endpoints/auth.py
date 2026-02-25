from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import (
    success_response,
)

from app.schemas.otp import SendOTPBody, SendOTPResponse, SendOTPRequest
from app.schemas.user import UserCreateResponse
from app.schemas.session import AccessTokenResponse

from app.services.otp_service import OTPService
from app.services.session_service import SessionService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def get_otp_service(db: AsyncSession = Depends(get_db)):
    return OTPService(db)

def get_session_Service(db: AsyncSession = Depends(get_db)):
    return SessionService(db)


@router.post("/send-otp")
async def send_otp(
    payload: SendOTPBody, otp_service: OTPService = Depends(get_otp_service)
):
    otp: SendOTPResponse = await otp_service.send_otp(payload)
    return success_response(
        message="OTP sent successfully",
        data=otp,
    )


@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    payload: SendOTPRequest,
    otp_service: OTPService = Depends(get_otp_service),
):
    result: UserCreateResponse = await otp_service.verify_otp(
        payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return success_response(
        message="OTP verified successfully",
        data=result,
        cookies=[
            {
                "key": "access_token",
                "value": result.token["access_token"],
                "max_age": result.token["expires_in"],
                "expires": result.token["expires_in"],
                "httponly": True,
                "secure": False,  # True in production
                "samesite": "lax",
            },
            {
                "key": "refresh_token",
                "value": result.token["refresh_token"],
                "max_age": 30 * 24 * 60 * 60,
                "expires": 30 * 24 * 60 * 60,
                "httponly": True,
                "secure": False,
                "samesite": "lax",
            },
        ],
    )

@router.post("/access-token")
async def access_token(
    payload: dict,
    session_service: SessionService = Depends(get_session_Service),
):
    res: AccessTokenResponse = await session_service.generate_access_token(payload["token"])
    return success_response(
        message="Token refreshed successfully",
        data=res,
        cookies=[
            {
                "key": "access_token",
                "value": res.access_token,
                "max_age": res.expires_in,
                "expires": res.expires_in,
                "httponly": True,
                "secure": False,  # True in production
                "samesite": "lax",
            }
        ]
    )
