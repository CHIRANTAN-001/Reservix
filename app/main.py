from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import check_db_connection, AsyncSessionLocal
from app.core.redis import check_redis_connection, redis_client
from app.core.response import (
    register_exception_handlers
)
from loguru import logger

import sys

from app.api.v1 import router as v1_router
from app.services.cache_rebuild_service import rebuild_section_inventory_cache
from app.repositories.section_inventory_repository import SectionInventoryRepository


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown logic
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # check database connection
        db_ok = await check_db_connection()
        if db_ok:
            logger.success("Database connection OK")
        else:
            logger.critical("Database connection FAILED")

        # check redis connection
        redis_ok = await check_redis_connection()
        if redis_ok:
            logger.success("Redis connection OK")
        else:
            logger.critical("Redis connection FAILED")

        async with AsyncSessionLocal() as db:
            inventory_repo = SectionInventoryRepository(db)
            
            await rebuild_section_inventory_cache(
                redis=redis_client,
                inventory_repo=inventory_repo
            )

        yield  # app runs here

    finally:
        logger.info(f"Shutting down {settings.APP_NAME} v{settings.APP_VERSION}")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    docs_url="/docs" if settings.APP_DEBUG else None,  # hide Swagger in production
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Setup Logging with Loguru
# ---------------------------------------------------------------------------
# Remove the default handler
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



# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(v1_router, prefix='/api/v1')

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)