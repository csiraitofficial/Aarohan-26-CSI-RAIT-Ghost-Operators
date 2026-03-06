import pytest
from app.core.orchestrator import NIDSOrchestrator
from app.models.schemas import SnifferConfig, MLModelConfig, PacketInfo

@pytest.fixture
def orchestrator():
    sniffer_cfg = SnifferConfig(interface="eth0")
    ml_cfg = MLModelConfig(model_path="app/ml_models/nids_model.joblib")
    return NIDSOrchestrator(sniffer_cfg, ml_cfg)

def test_orchestrator_initialization(orchestrator):
    assert orchestrator.capture_engine is not None
    assert orchestrator.ml_engine is not None
    assert orchestrator.is_running is False

def test_packet_processing_pipeline(orchestrator):
    packet = PacketInfo(
        source_ip="192.168.1.1",
        dest_ip="192.168.1.2",
        protocol="TCP",
        packet_length=64,
        payload_size=0
    )
    # Process packet shouldn't raise exceptions
    orchestrator._process_packet(packet)
    assert orchestrator.packets_processed == 1

def test_security_level_stats(orchestrator):
    stats = orchestrator.get_system_status()
    assert stats.packets_captured == 0
    assert stats.memory_usage > 0
