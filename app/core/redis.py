from redis.asyncio import Redis, from_url
from typing import cast, Awaitable

from app.core.config import settings

redis_client: Redis = from_url(
    settings.REDIS_URL,
    decode_responses=False
)

# ---------------------------------------------------------------------------
# Redis client factory
# ---------------------------------------------------------------------------
async def get_redis_client() -> Redis:
    return redis_client


async def check_redis_connection() -> bool:
    try:
        return await cast(Awaitable[bool], redis_client.ping())
    except Exception:
        return False