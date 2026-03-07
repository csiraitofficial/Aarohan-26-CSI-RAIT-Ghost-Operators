"""
Application Configuration — loaded from environment variables using pydantic-settings.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    CORS_ORIGINS: str = "*"

    JWT_SECRET: str = "change-me-to-a-strong-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7
    API_KEY: Optional[str] = None
    ENABLE_API_AUTH: bool = False

    INTERFACE: str = "Wi-Fi" if os.name == "nt" else "eth0"
    PACKET_COUNT: int = 0
    CAPTURE_TIMEOUT: int = 0
    CAPTURE_WORKERS: int = 4
    MODEL_PATH: str = "app/ml_models/nids_model.joblib"
    CONFIDENCE_THRESHOLD: float = 0.8
    MODEL_TYPE: str = "random_forest"
    ENABLE_DL_MODELS: bool = False

    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DB_NAME: str = "nids_advanced"
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/nids.log"

    GEOIP_DB_PATH: str = "data/GeoLite2-City.mmdb"

    IPS_ENABLED: bool = False
    IPS_AUTO_BLOCK: bool = False
    IPS_BLOCK_DURATION_MINUTES: int = 60
    ABUSEIPDB_API_KEY: Optional[str] = None
    VIRUSTOTAL_API_KEY: Optional[str] = None

    MAX_ALERTS: int = 50000
    MAX_PACKETS_BUFFER: int = 20000
    CORRELATION_WINDOW_MINUTES: int = 5

    # Blockchain (Industrial Hardening)
    BLOCKCHAIN_ENABLED: bool = True
    BLOCKCHAIN_RPC_URL: str = "https://rpc-amoy.polygon.technology"
    BLOCKCHAIN_CONTRACT_ADDRESS: str = "0x45ad3803Af70d36d872915AeA8da6596F4bDFd76"
    BLOCKCHAIN_CONSENSUS_ADDRESS: str = "0xD3041AB8c5A6d984ac360054130459C8AC45b20B"
    BLOCKCHAIN_PRIVATE_KEY: Optional[str] = None

    # Hardware Resilience
    NIDS_SAFE_MODE: bool = False

    @property
    def mongodb_url(self) -> str:
        """Build MongoDB connection URL."""
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            return (
                f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}"
                f"@{self.MONGODB_HOST}:{self.MONGODB_PORT}"
            )
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}"

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS CSV into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()


def get_settings() -> Settings:
    return settings
