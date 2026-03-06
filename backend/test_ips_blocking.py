
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

async def test_ips():
    print("--- Testing IPS Engine (Auto-Block) ---")
    await db_manager.connect()
    
    # Setup Orchestrator
    orchestrator = NIDSOrchestrator(
        SnifferConfig(interface="Wi-Fi"),
        MLModelConfig(model_path="app/ml_models/nids_model.joblib"),
        IPSConfig(enabled=True, auto_block=True)
    )
    orchestrator.is_running = True
    
    source_ip = "192.168.1.200"
    print(f"Injecting 60 SYN packets from {source_ip} to trigger block...")
    
    for i in range(100):
        packet = PacketInfo(
            source_ip=source_ip,
            dest_ip="10.177.71.189",
            protocol="TCP",
            source_port=10000 + i,
            dest_port=80,
            packet_length=64,
            payload_size=0,
            tcp_flags="S"
        )
        orchestrator._process_packet(packet)
    
    print("Waiting for stateful window to process...")
    await asyncio.sleep(11) # Wait for the 10s window cleanup in track_stateful
    
    # Verification
    is_blocked = orchestrator.ips_engine.is_blocked(source_ip)
    print(f"IPS Status: {source_ip} is {'BLOCKED' if is_blocked else 'NOT BLOCKED'}")
    
    alert = await db_manager.db.alerts.find_one({"source_ip": source_ip})
    if alert:
        print(f"Alert Recorded: {alert['description']}")
        print(f"Integrity Hash stored: {alert['integrity_hash'][:20]}...")
        
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ips())
