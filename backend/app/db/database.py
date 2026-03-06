"""
Database Layer — Async MongoDB integration using Motor.

Upgrades over original:
  - Truly asynchronous operations (original used synchronous pymongo in some places)
  - Connection pooling and lifespan management
  - Indexes for high-performance alert querying
"""

import logging
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

from app.utils.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Verify connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
            
            # Create indexes
            await self.create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.db = None

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_indexes(self):
        if self.db is not None:
            # Alerts indexes
            await self.db.alerts.create_index([("timestamp", -1)])
            await self.db.alerts.create_index([("severity", 1)])
            await self.db.alerts.create_index([("source_ip", 1)])
            await self.db.alerts.create_index([("is_resolved", 1)])
            
            # Packets indexes (capped collection or TTL index recommended for performance)
            await self.db.packets.create_index([("timestamp", -1)], expireAfterSeconds=86400 * 7) # 7 days TTL
            
            logger.info("Database indexes created")

    # ---- Alerts ----
    async def insert_alert(self, alert_data: Dict[str, Any]):
        if self.db is not None:
            await self.db.alerts.insert_one(alert_data)

    async def get_alerts(self, filters: Dict[str, Any], limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        if self.db is None:
            return []
        cursor = self.db.alerts.find(filters).sort("timestamp", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_alerts(self, filters: Dict[str, Any]) -> int:
        if self.db is None:
            return 0
        return await self.db.alerts.count_documents(filters)

    # ---- Packets ----
    async def insert_packet(self, packet_data: Dict[str, Any]):
        if self.db is not None:
            await self.db.packets.insert_one(packet_data)

    async def get_packets(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        if self.db is None:
            return []
        cursor = self.db.packets.find(filters).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

# Singleton
db_manager = DatabaseManager()
