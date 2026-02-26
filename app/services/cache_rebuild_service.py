from app.core.redis import Redis
from app.repositories.section_inventory_repository import SectionInventoryRepository
from app.services.event_service import calculate_ttl
from loguru import logger

async def rebuild_section_inventory_cache(
    redis: Redis,
    inventory_repo: SectionInventoryRepository
):
    """
    Rebuild Redis section inventory keys if missing.
    """
    
    sections = await inventory_repo.get_all_inventory()
    
    pipe = redis.pipeline()
    
    for section in sections:
        response = {
            "event_id": str(section["event_id"]),
            "section_id": str(section["section_id"]),
            "available_capacity": int(section["available_capacity"]),
            "ttl": calculate_ttl(section["event_date"])
        }
        
        section_inventory_key = f"section:{response['event_id']}:{response['section_id']}"
        pipe.set(
            section_inventory_key,
            response["available_capacity"],
            ex=response["ttl"],
            nx=True
        )
        
    await pipe.execute()
    
    logger.success("Section inventory cache rebuilt")
    