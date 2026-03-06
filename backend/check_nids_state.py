
import sys
import os
import asyncio
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.orchestrator import NIDSOrchestrator
from app.models.schemas import SnifferConfig, MLModelConfig

async def check_stats():
    # This might fail if another process is holding the sniffer, 
    # but we just want to see if we can access the shared state or at least see the current config.
    # Actually, let's try to find the running process or check the DB.
    
    from app.db.database import db_manager
    await db_manager.connect()
    
    alert_count = await db_manager.db.alerts.count_documents({})
    packet_count = await db_manager.db.packets.count_documents({})
    block_count = await db_manager.db.blocks.count_documents({})
    
    print(f"Total Alerts in DB: {alert_count}")
    print(f"Total Packets in DB: {packet_count}")
    print(f"Total Blocks in DB: {block_count}")
    
    last_alerts = await db_manager.db.alerts.find().sort("timestamp", -1).limit(5).to_list(length=5)
    print("\nLatest 5 Alerts:")
    for a in last_alerts:
        print(f"{a['timestamp']} - {a['severity']} - {a['description']} (from {a['source_ip']})")

    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(check_stats())
