import asyncio 
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_client

from sqlalchemy import text

from app.models.bookings import BookingStatus

import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    level="DEBUG",
    # Added {elapsed} after the timestamp
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> (<magenta>{elapsed}</magenta>) | <level>{level: <7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    backtrace=True,
    diagnose=True,
    enqueue=True
)

INTERVAL = 40
BATCH_SIZE = 100

async def expiry_loop():
    redis = await get_redis_client()
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                update_query = text("""
                    UPDATE bookings
                    SET status = :updated_status
                    WHERE status = :previous_status
                    AND expires_at < EXTRACT(EPOCH FROM NOW())
                    RETURNING id, event_id, section_id, seats_requested, user_id, status, created_at, updated_at;
                """)
                rows = await db.execute(
                    update_query,{
                        "updated_status": BookingStatus.EXPIRED,
                        "previous_status": BookingStatus.HOLD
                    }
                )
                
                bookings = rows.mappings().all()
                print(bookings)
                
                for booking in bookings:
                    cached_key = f"section:{booking['event_id']}:{booking['section_id']}"
                    event_cached_key = f"event:{booking['event_id']}"
                    booking_cached_key = f"booking:{booking['id']}"
                    
                    try:
                        pipe = await redis.pipeline()
                        
                        pipe.incrby(cached_key, int(booking['seats_requested']))
                        pipe.delete(event_cached_key)
                        pipe.delete(booking_cached_key)
                        
                        await pipe.execute()
                        logger.success(f"Redis updated for key: {cached_key}")
                    except Exception as redis_err:
                        logger.error(f"Redis error for {cached_key}: {redis_err}")
            
                await db.commit()
        except Exception as e:
            logger.error(f"Error in expiry loop: {e}")
    
        await asyncio.sleep(INTERVAL)
    
if __name__ == "__main__":
    asyncio.run(expiry_loop())
            