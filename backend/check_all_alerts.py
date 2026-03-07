import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_all_alerts():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["nids_advanced"]
    alerts_col = db["alerts"]
    
    # Get the last 5 alerts regardless of time
    cursor = alerts_col.find().sort("timestamp", -1).limit(5)
    alerts = await cursor.to_list(length=5)
    
    if not alerts:
        print("No alerts found in the database.")
        return
        
    for alert in alerts:
        print(f"[{alert.get('timestamp')}] {alert.get('severity', 'N/A').upper()} - {alert.get('category', 'N/A')}")
        print(f"  Source: {alert.get('source_ip', 'N/A')} -> Dest: {alert.get('dest_ip', 'N/A')}")
        print(f"  Rule: {alert.get('rule_id', 'N/A')}")
        print(f"  Message: {alert.get('message', 'N/A')}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(check_all_alerts())
