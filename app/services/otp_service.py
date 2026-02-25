from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.otp_repository import OTPRepository
from app.repositories.user_respository import UserRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.otp import SendOTPRequest, SendOTPResponse, SendOTPBody
from app.schemas.user import UserCreateResponse
from app.schemas.session import SessionCreate

from app.core.config import settings
from typing import Optional

import random
import bcrypt
import secrets
import string
import jwt
import time

from app.core.response import NotFoundException


def generate_otp() -> str:
    """
    Generates a random 4-digit OTP.

    Returns:
        str: A random 4-digit OTP.
    """
    return str(random.randint(1000, 9999))


def generate_refresh_token() -> str:
    token = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
    )
    return token


def generate_access_token(sub: str, aud: str) -> str:
    token = {
        "iss": "http://localhost:8000",
        "sub": sub,
        "phone": aud,
        "exp": time.time() + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        "iat": time.time(),
    }
    jwt_token = jwt.encode(
        payload=token, key=settings.SECRET_KEY, algorithm=settings.HASHING_ALG
    )
    return jwt_token


class OTPService:
    def __init__(self, db: AsyncSession) -> None:
        self.otp_repo = OTPRepository(db)
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    async def send_otp(self, payload: SendOTPBody) -> SendOTPResponse:
        """
        Sends a random 4-digit OTP to the user's phone number.

        Args:
            payload (SendOTPBody): The request body containing the country code and phone number.

        Returns:
            SendOTPResponse: The response containing the OTP.

        Raises:
            Exception: If the OTP could not be sent.
        """
        otp = generate_otp()
        hashed_otp = bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt())
        data = SendOTPRequest(
            otp=hashed_otp.decode("utf-8"),
            country_code=payload.country_code,
            phone_number=payload.phone_number,
        )

        result = await self.otp_repo.send_otp(data)
        result["otp"] = otp
        if not result:
            raise Exception("Failed to send OTP")
        return SendOTPResponse.model_validate(result)

    async def _issue_tokens(
        self,
        user: dict,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> dict:

        access_token = generate_access_token(
            sub=str(user["id"]),
            aud=user["phone_number"],
        )

        refresh_token = generate_refresh_token()

        await self.session_repo.create(
            SessionCreate(
                user_id=user["id"],
                token=refresh_token,
                ipAddress=ip_address,
                userAgent=user_agent,
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        }

    async def verify_otp(
        self,
        payload: SendOTPRequest,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> UserCreateResponse:
        # Transaction Begin
        """
        Verifies the OTP sent to the user's phone number.

        Args:
            payload (SendOTPRequest): The request body containing the country code, phone number, and OTP.

        Returns:
            UserCreateResponse: The response containing the user data and token.

        Raises:
            NotFoundException: If the phone number or OTP is incorrect.
        """
        async with self.user_repo.db.begin():
            # check if user exist or not
            # check if there's an otp  for this phone number
            result = await self.otp_repo.get_otp(payload)
            if result is None:
                raise NotFoundException("Incorrect Phone Number")

            # check if otp is correct
            verify_otp = bcrypt.checkpw(
                payload.otp.encode("utf-8"), result["otp"].encode("utf-8")
            )
            if not verify_otp:
                # If OTP is incorrect throw exception
                # Transaction Rollback
                raise NotFoundException("Incorrect OTP")

            user = await self.user_repo.create(payload)

            if user:
                token_data = await self._issue_tokens(
                    user,
                    ip_address,
                    user_agent,
                )
                user["token"] = token_data


            return UserCreateResponse(
                **user
            )
