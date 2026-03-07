import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

async def check_alerts():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["nids_db"]
    alerts_col = db["alerts"]
    
    # Get alerts from the last 10 minutes
    ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
    cursor = alerts_col.find({"timestamp": {"$gte": ten_mins_ago}}).sort("timestamp", -1).limit(10)
    
    alerts = await cursor.to_list(length=10)
    if not alerts:
        print("No alerts found in the last 10 minutes.")
        return
        
    for alert in alerts:
        print(f"[{alert['timestamp']}] {alert['severity'].upper()} - {alert['category']}")
        print(f"  Source: {alert['source_ip']} -> Dest: {alert['dest_ip']}")
        print(f"  Rule: {alert.get('rule_id', 'N/A')}")
        print(f"  Message: {alert['message']}")
        if 'mitre' in alert:
            print(f"  MITRE: {alert['mitre']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(check_alerts())
