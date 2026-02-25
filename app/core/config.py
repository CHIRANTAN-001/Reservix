from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "REZZ"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = False
    ENVIRONMENT: str = "development"
    PORT: int = 4000

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydb"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USER: str = "user"
    REDIS_PASSWORD: str = "password"

    # Security
    SECRET_KEY: str = "secret"
    HASHING_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = []
    
    # Computed - not efrom env, built from above config
    @property
    def DATABASE_URL(self) -> str:
        # asyncpg driver for async SQLAlchemy
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def REDIS_URL(self) -> str:
        # asyncpg driver for async SQLAlchemy
        return (
            f"rediss://{self.REDIS_USER}:{self.REDIS_PASSWORD}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}"
        )
        
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
# single instnce of settings ( import everywhere)
settings = Settings()
