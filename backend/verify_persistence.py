
import sys
import os
import asyncio
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.db.database import db_manager

async def verify_persistence():
    print("--- Final Persistence & Integrity Analysis ---")
    await db_manager.connect()
    
    print("\n[MongoDB Data]")
    alerts = await db_manager.db.alerts.find().sort("timestamp", -1).limit(10).to_list(length=10)
    for a in alerts:
        print(f"- {a['timestamp']} | Type: {a['detection_type']} | IP: {a['source_ip']} | Hash: {a.get('integrity_hash', 'MISSING')[:16]}...")

    print("\n[Analysis]")
    if all(a.get('integrity_hash') for a in alerts):
        print("PASS: All latest alerts have cryptographic integrity hashes.")
    else:
        print("FAIL: Some alerts are missing integrity hashes.")

    blocks = await db_manager.db.blocks.count_documents({})
    print(f"\nTotal Active Blocks in DB: {blocks}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(verify_persistence())
