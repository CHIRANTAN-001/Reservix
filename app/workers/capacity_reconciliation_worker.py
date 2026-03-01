import asyncio
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_client
from sqlalchemy import text
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
    enqueue=True,
)

INTYERVAL = 120  # in seconds


async def capacity_reconciliation_worker():
    redis = await get_redis_client()

    while True:
        # 1. Get the event_id and section_id form the bookings table WHERE status = 'CONFIRMED'
        # 2. Get the total_capacity from the section_inventory table
        # 3. Update the available_capacity in the redis cache  if it doesn't match
        try:
            async with AsyncSessionLocal() as db:
                available_capacity_query = text("""
                    SELECT
                        event_id,
                        section_id,
                        SUM(seats_requested) as used_seats
                    FROM bookings
                    WHERE status IN ('CONFIRMED', 'HOLD')
                    GROUP BY (event_id, section_id);
                """)

                inventory_query = text("""
                    SELECT 
                        total_capacity
                    FROM section_inventory
                    WHERE section_id = :section_id;                       
                """)

                rows = await db.execute(available_capacity_query)
                bookings = rows.mappings().all()

                for booking in bookings:
                    event_id = str(booking["event_id"])
                    section_id = str(booking["section_id"])
                    used_seats = int(booking["used_seats"])

                    section_cached_key = f"section:{event_id}:{section_id}"
                    available_capacity_in_cache = await redis.get(section_cached_key)

                    inventory_rows = await db.execute(
                        inventory_query, {"section_id": section_id}
                    )
                    inventory = inventory_rows.mappings().one()

                    total_capacity = inventory["total_capacity"]

                    available_capacity = total_capacity - used_seats

                    if available_capacity != int(available_capacity_in_cache):
                        logger.info(
                            f"Capacity mismatch: Updating capacity for {section_cached_key} from {available_capacity_in_cache} to {available_capacity}"
                        )
                        await redis.set(section_cached_key, available_capacity)
        except Exception as e:
            logger.error(f"Error in capacity reconciliation worker: {e}")

        await asyncio.sleep(INTYERVAL)


if __name__ == "__main__":
    asyncio.run(capacity_reconciliation_worker())
