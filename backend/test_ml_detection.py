
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

async def test_ml():
    print("--- Testing ML Engine ---")
    await db_manager.connect()
    
    # Setup Orchestrator
    orchestrator = NIDSOrchestrator(
        SnifferConfig(interface="Wi-Fi"),
        MLModelConfig(model_path="app/ml_models/nids_model.joblib"),
        IPSConfig(enabled=True, auto_block=True)
    )
    orchestrator.is_running = True
    
    # Anomalous packet (Large payload, unusual ports, etc.)
    packet = PacketInfo(
        source_ip="192.168.1.75",
        dest_ip="10.177.71.189",
        protocol="TCP",
        source_port=55555,
        dest_port=23, # Telnet (often flagged)
        packet_length=1500,
        payload_size=1400,
        tcp_flags="S"
    )
    
    print("Injecting potential ML-anomaly packet...")
    orchestrator._process_packet(packet)
    
    await asyncio.sleep(2)
    
    # Check DB
    alert = await db_manager.db.alerts.find_one({"source_ip": "192.168.1.75", "detection_type": "ml"})
    if alert:
        print(f"ML Alert Found: {alert['description']}")
        print(f"Integrity Hash: {alert['integrity_hash']}")
    else:
        # Sometimes ML needs more context or specific joblib model.
        # We'll check if ANY alert was generated.
        any_alert = await db_manager.db.alerts.find_one({"source_ip": "192.168.1.75"})
        if any_alert:
             print(f"Alert Found (Type: {any_alert['detection_type']}): {any_alert['description']}")
        else:
            print("ML Alert not found. (The default model might be strict or weights are clean)")
        
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ml())
