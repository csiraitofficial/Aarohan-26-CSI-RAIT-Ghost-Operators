
import sys
import os
import time
import asyncio
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app.core.orchestrator import NIDSOrchestrator
from app.models.schemas import SnifferConfig, MLModelConfig, IPSConfig, PacketInfo

async def simulate():
    print("Starting Security Simulation...")
    
    # 1. Setup Orchestrator (Dry run mode / Disable live capture)
    sniffer_cfg = SnifferConfig(interface="Wi-Fi")
    ml_cfg = MLModelConfig(model_path="app/ml_models/nids_model.joblib", confidence_threshold=0.8)
    ips_cfg = IPSConfig(enabled=True, auto_block=True)
    
    orchestrator = NIDSOrchestrator(sniffer_cfg, ml_cfg, ips_cfg)
    
    # Connect DB
    from app.db.database import db_manager
    await db_manager.connect()
    
    print("Injecting 60 SYN packets from the same source IP (192.168.1.100)...")
    
    # 2. Generate 60 SYN packets for the same IP (Exceeding the threshold of 50)
    source_ip = "192.168.1.100"
    for i in range(60):
        packet = PacketInfo(
            source_ip=source_ip,
            dest_ip="10.177.71.189",
            protocol="TCP",
            source_port=12345 + i,
            dest_port=443,
            packet_length=64,
            tcp_flags="S",  # SYN flag
            payload_size=0
        )
        orchestrator._process_packet(packet)
        if i % 10 == 0:
            print(f"   Processed {i} packets...")
        time.sleep(0.01) # Small delay
    
    print("\n⏳ Waiting for background synchronization...")
    await asyncio.sleep(2)
    
    # 3. Verify the state
    print("\nVerification Results:")
    
    # Check IPS State
    is_blocked = orchestrator.ips_engine.is_blocked(source_ip)
    print(f"   [IPS] Is {source_ip} blocked? {'YES' if is_blocked else 'NO'}")
    
    # Check Alerts
    alert_count = await db_manager.db.alerts.count_documents({"source_ip": source_ip})
    print(f"   [DB] Alerts for {source_ip}: {alert_count}")
    
    if alert_count > 0:
        alert = await db_manager.db.alerts.find_one({"source_ip": source_ip})
        print(f"   [Integrity] Alert Hash: {alert.get('integrity_hash')}")
        print(f"   [Detection] Description: {alert.get('description')}")
    
    await db_manager.disconnect()
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(simulate())
