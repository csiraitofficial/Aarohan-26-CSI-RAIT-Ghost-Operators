import asyncio
from app.models.schemas import PacketInfo, SnifferConfig, MLModelConfig
from app.core.orchestrator import NIDSOrchestrator
from app.utils.config import get_settings
from datetime import datetime
import time

async def trigger_nids():
    settings = get_settings()
    s_config = SnifferConfig(interface="Loopback Pseudo-Interface 1")
    m_config = MLModelConfig(model_path=settings.MODEL_PATH)
    orc = NIDSOrchestrator(sniffer_config=s_config, ml_config=m_config)
    orc.start()
    await asyncio.sleep(2)
    
    print("--- INJECTING SQL INJECTION ---")
    sqli_pkt = PacketInfo(
        timestamp=datetime.now(),
        source_ip="10.0.0.1",
        dest_ip="192.168.5.63",
        protocol="TCP",
        source_port=12345,
        dest_port=80,
        packet_length=150,
        payload_size=50,
        tcp_flags="PA",
        payload_hex="/?id=1' OR '1'='1".encode().hex(),
        ttl=64
    )
    orc._process_packet(sqli_pkt)
    
    await asyncio.sleep(1)
    
    print("--- INJECTING COMMAND INJECTION ---")
    cmd_pkt = PacketInfo(
        timestamp=datetime.now(),
        source_ip="10.0.0.2",
        dest_ip="192.168.5.63",
        protocol="TCP",
        source_port=54321,
        dest_port=80,
        packet_length=150,
        payload_size=50,
        tcp_flags="PA",
        payload_hex="/?cmd=cat /etc/passwd".encode().hex(),
        ttl=64
    )
    orc._process_packet(cmd_pkt)
    
    print("--- INJECTING SYN FLOOD ---")
    for i in range(55):
        syn_pkt = PacketInfo(
            timestamp=datetime.now(),
            source_ip="10.0.0.3",
            dest_ip="192.168.5.63",
            protocol="TCP",
            source_port=random_port(i),
            dest_port=80,
            packet_length=60,
            payload_size=0,
            tcp_flags="S",
            ttl=64
        )
        orc._process_packet(syn_pkt)
        
    await asyncio.sleep(3)
    orc.stop()
    print("Injection complete.")

def random_port(i):
    return 10000 + i

if __name__ == "__main__":
    asyncio.run(trigger_nids())
