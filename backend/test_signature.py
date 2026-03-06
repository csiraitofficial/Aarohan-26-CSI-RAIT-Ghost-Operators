
import sys
import os
import asyncio
import time
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.orchestrator import NIDSOrchestrator
from app.models.schemas import SnifferConfig, MLModelConfig, IPSConfig, PacketInfo
from app.db.database import db_manager

async def test_signature():
    print("--- Testing Signature Engine ---")
    await db_manager.connect()
    
    # Setup Orchestrator
    orchestrator = NIDSOrchestrator(
        SnifferConfig(interface="Wi-Fi"),
        MLModelConfig(model_path="app/ml_models/nids_model.joblib"),
        IPSConfig(enabled=True, auto_block=True)
    )
    orchestrator.is_running = True
    
    # Known Signature Trigger: ICMP Flood or similar
    # Let's find a rule in signature_engine.py later, but for now we'll use a generic packet 
    # that usually matches based on content or flags.
    # Looking at the codebase, "Generic TCP Port Scan" or "ICMP Flood" are common.
    
    packet = PacketInfo(
        source_ip="192.168.1.50",
        dest_ip="10.177.71.189",
        protocol="TCP",
        dest_port=23,
        packet_length=64,
        payload_size=0,
        payload_hex="" 
    )
    
    print("Injecting Signature-triggering Telnet packet...")
    orchestrator._process_packet(packet)
    
    # Debug: Check orchestrator internal counters
    print(f"Packets processed by orchestrator: {orchestrator.packets_processed}")
    
    # Wait for async DB task
    print("Waiting 5s for persistence...")
    await asyncio.sleep(5)
    
    # Check DB
    alert = await db_manager.db.alerts.find_one({"source_ip": "192.168.1.50", "detection_type": "signature"})
    if alert:
        print(f"Alert Found: {alert['description']}")
        print(f"Integrity Hash: {alert['integrity_hash']}")
    else:
        print("Signature Alert not found in DB.")
        
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_signature())
