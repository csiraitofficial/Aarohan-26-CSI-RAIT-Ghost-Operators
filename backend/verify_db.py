import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def verify():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['nids_advanced']
    
    count = await db.alerts.count_documents({})
    print(f"Total alerts in 'nids_advanced.alerts': {count}")
    
    print("\nLatest 10 alerts:")
    cursor = db.alerts.find().sort('timestamp', -1).limit(10)
    async for alert in cursor:
        ts = alert.get('timestamp')
        sev = alert.get('severity')
        desc = alert.get('description')
        src = alert.get('source_ip')
        print(f"[{ts}] {sev.upper()} - {src} -> {desc}")

if __name__ == "__main__":
    asyncio.run(verify())
