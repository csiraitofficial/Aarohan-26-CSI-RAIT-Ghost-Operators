"""
NIDS Orchestrator — central coordinator for all subsystems.

Upgrades over original:
  - Integrates FlowAggregator for flow-level analysis
  - Periodic flow flush in a background thread
  - WebSocket broadcast wiring
  - Blockchain client is optional (pluggable)
"""

import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging

from app.core.capture_engine import CaptureEngine
from app.core.flow_aggregator import FlowAggregator
from app.core.alert_manager import AlertManager
from app.core.ips_manager import IPSManager
from app.detection.ml_engine import MLEngine
from app.detection.signature_engine import SignatureEngine
from app.detection.eta_engine import eta_engine
from app.detection.correlation_engine import correlation_engine
from app.intelligence.threat_feeds import threat_intel
from app.intelligence.geoip import geoip_lookup
from app.models.schemas import (
    PacketInfo, SnifferConfig, MLModelConfig, IPSConfig,
    SystemStatus, DetectionType,
)

logger = logging.getLogger(__name__)


class NIDSOrchestrator:
    """Central coordinator that wires all NIDS subsystems together."""

    def __init__(
        self,
        sniffer_config: SnifferConfig,
        ml_config: MLModelConfig,
        ips_config: Optional[IPSConfig] = None,
        alert_callback: Optional[Callable] = None,
        ws_broadcast: Optional[Callable] = None,
    ):
        self.sniffer_config = sniffer_config
        self.ml_config = ml_config

        # Core engines
        self.capture_engine = CaptureEngine(sniffer_config)
        self.flow_aggregator = FlowAggregator(flow_timeout=120.0)
        self.ml_engine = MLEngine(ml_config)
        self.signature_engine = SignatureEngine()
        self.ips_manager = IPSManager(ips_config)
        self.alert_manager = AlertManager(
            alert_callback=alert_callback,
            ws_broadcast=ws_broadcast,
        )
        
        # Phase 2 Advanced Engines
        self.eta_engine = eta_engine
        self.correlation_engine = correlation_engine
        self.threat_intel = threat_intel
        self.geoip = geoip_lookup

        # State
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.packets_processed = 0
        self.alerts_generated = 0
        self.ml_predictions = 0
        self.signature_matches = 0

        # Performance
        self._perf = {
            "avg_processing_time": 0.0,
            "max_processing_time": 0.0,
            "min_processing_time": float("inf"),
            "total_processing_time": 0.0,
        }
        self._last_cleanup = time.time()
        self._flow_flush_thread: Optional[threading.Thread] = None

    # ----------------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------------

    def start(self) -> bool:
        if self.is_running:
            logger.warning("NIDS already running")
            return False

        self.is_running = True
        self.start_time = datetime.now()
        self.packets_processed = 0
        self.alerts_generated = 0
        self.ml_predictions = 0
        self.signature_matches = 0
        self._perf = {
            "avg_processing_time": 0.0,
            "max_processing_time": 0.0,
            "min_processing_time": float("inf"),
            "total_processing_time": 0.0,
        }

        if not self.capture_engine.start(callback=self._process_packet):
            logger.error("Failed to start capture engine")
            self.is_running = False
            return False

        # Background flow flush
        self._flow_flush_thread = threading.Thread(target=self._flow_flush_loop, daemon=True)
        self._flow_flush_thread.start()

        logger.info("NIDS system started")
        return True

    def stop(self) -> bool:
        if not self.is_running:
            return False
        self.is_running = False
        self.capture_engine.stop()
        logger.info("NIDS system stopped")
        return True

    # ----------------------------------------------------------------
    # Packet Processing Pipeline
    # ----------------------------------------------------------------

    def _process_packet(self, packet: PacketInfo):
        """Main processing pipeline for each captured packet."""
        if not self.is_running:
            return

        t0 = time.time()
        try:
            self.packets_processed += 1

            # IPS cleanup
            if time.time() - self._last_cleanup > 60:
                self.ips_manager.cleanup_expired()
                self._last_cleanup = time.time()

            # Skip blocked IPs
            if self.ips_manager.is_blocked(packet.source_ip):
                return

            # Feed to flow aggregator
            self.flow_aggregator.process_packet(packet)

            # ML detection (packet-level)
            ml_result = self._run_ml(packet)

            # Signature detection
            sig_results = self._run_signatures(packet)

            # ETA detection
            eta_result = self.eta_engine.process_packet(packet)
            if eta_result:
                sig_results.append(eta_result)

            # Generate alerts
            alerts = self._generate_alerts(packet, ml_result, sig_results)
            
            # Phase 2: Correlation
            for alert in alerts:
                if alert:
                    incident = self.correlation_engine.correlate(alert)
                    if incident:
                        # Log/Broadcast incident
                        logger.warning(f"INCIDENT: {incident.title}")

            # Performance tracking
            elapsed = time.time() - t0
            self._update_perf(elapsed)

        except Exception as e:
            logger.error(f"Packet processing error: {e}")

    def _run_ml(self, packet: PacketInfo) -> Dict[str, Any]:
        try:
            result = self.ml_engine.predict_packet(packet)
            self.ml_predictions += 1
            return result
        except Exception as e:
            logger.error(f"ML engine error: {e}")
            return {"is_anomalous": False, "confidence": 0.0, "severity": "info"}

    def _run_signatures(self, packet: PacketInfo) -> List[Dict[str, Any]]:
        try:
            results = self.signature_engine.detect(packet)
            self.signature_matches += len(results)
            return results
        except Exception as e:
            logger.error(f"Signature engine error: {e}")
            return []

    def _generate_alerts(self, packet: PacketInfo, ml: Dict, sigs: List[Dict]) -> List[Alert]:
        created_alerts = []
        highest = "info"

        if ml.get("is_anomalous"):
            a = self.alert_manager.create_ml_alert(ml, packet)
            if a:
                created_alerts.append(a)
                highest = a.severity

        for sig in sigs:
            a = self.alert_manager.create_signature_alert(sig, packet)
            if a:
                created_alerts.append(a)
                if a.severity == "critical":
                    highest = "critical"
                elif a.severity == "high" and highest != "critical":
                    highest = "high"

        # Hybrid alert
        if ml.get("is_anomalous") and sigs:
            best_sig = max(sigs, key=lambda s: s.get("confidence", 0))
            a = self.alert_manager.create_hybrid_alert(ml, best_sig, packet)
            if a:
                created_alerts.append(a)

        # IPS auto-block on critical
        if highest == "critical" and self.ips_manager.config.auto_block:
            self.ips_manager.block_ip(
                packet.source_ip,
                duration_minutes=self.ips_manager.config.block_duration_minutes,
                reason="Critical threat auto-blocked by NIDS",
            )

        self.alerts_generated += len(created_alerts)
        return created_alerts

    # ----------------------------------------------------------------
    # Flow Flush
    # ----------------------------------------------------------------

    def _flow_flush_loop(self):
        """Periodically flush expired flows and run flow-level ML."""
        while self.is_running:
            try:
                time.sleep(30)
                completed_flows = self.flow_aggregator.flush_expired()
                for flow in completed_flows:
                    result = self.ml_engine.predict_flow(flow)
                    if result.get("is_anomalous"):
                        # Create a synthetic packet for the alert manager
                        pkt = PacketInfo(
                            timestamp=flow.end_time,
                            source_ip=flow.source_ip,
                            dest_ip=flow.dest_ip,
                            protocol=flow.protocol,
                            source_port=flow.source_port,
                            dest_port=flow.dest_port,
                            packet_length=flow.total_bytes,
                            payload_size=flow.total_bytes,
                        )
                        result["description"] = (
                            f"Flow anomaly: {flow.total_packets} pkts, "
                            f"{flow.total_bytes} bytes, {flow.duration_seconds:.1f}s"
                        )
                        self.alert_manager.create_ml_alert(result, pkt)
                        self.alerts_generated += 1
            except Exception as e:
                logger.error(f"Flow flush error: {e}")

    # ----------------------------------------------------------------
    # Performance
    # ----------------------------------------------------------------

    def _update_perf(self, elapsed: float):
        p = self._perf
        p["total_processing_time"] += elapsed
        p["min_processing_time"] = min(p["min_processing_time"], elapsed)
        p["max_processing_time"] = max(p["max_processing_time"], elapsed)
        p["avg_processing_time"] = p["total_processing_time"] / max(self.packets_processed, 1)

    # ----------------------------------------------------------------
    # Status & Stats
    # ----------------------------------------------------------------

    def get_system_status(self) -> SystemStatus:
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        try:
            mem = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent(interval=0.1)
        except Exception:
            mem = cpu = 0.0
        return SystemStatus(
            is_running=self.is_running,
            uptime=uptime,
            packets_captured=self.capture_engine.packets_captured,
            flows_aggregated=self.flow_aggregator.total_flows_completed,
            alerts_generated=self.alerts_generated,
            ml_predictions=self.ml_predictions,
            signature_matches=self.signature_matches,
            memory_usage=mem,
            cpu_usage=cpu,
        )

    def get_detailed_stats(self) -> Dict[str, Any]:
        return {
            "system_status": self.get_system_status().model_dump(),
            "capture_stats": self.capture_engine.get_stats(),
            "flow_stats": self.flow_aggregator.get_stats(),
            "ml_stats": self.ml_engine.get_stats(),
            "signature_stats": self.signature_engine.get_stats(),
            "alert_stats": self.alert_manager.get_stats(),
            "ips_stats": self.ips_manager.get_stats(),
            "performance_stats": self._perf,
            "component_health": {
                "capture": self.capture_engine.is_running,
                "ml": self.ml_engine.is_loaded,
                "signatures": len(self.signature_engine.rules) > 0,
                "alerts": True,
                "ips": True,
            },
        }

    # ----------------------------------------------------------------
    # Delegated APIs
    # ----------------------------------------------------------------

    def get_recent_packets(self, limit: int = 100):
        return self.capture_engine.get_recent_packets(limit)

    def get_alerts(self, limit: int = 100, **filters):
        return self.alert_manager.get_alerts(limit=limit, **filters)

    def resolve_alert(self, alert_id: str, resolved_by: str = "", notes: str = ""):
        return self.alert_manager.resolve_alert(alert_id, resolved_by, notes)

    def clear_alerts(self, older_than_days: Optional[int] = None):
        if older_than_days:
            self.alert_manager.clear_alerts(timedelta(days=older_than_days))
        else:
            self.alert_manager.clear_alerts()

    def export_alerts(self, fmt: str = "json", filepath: Optional[str] = None):
        return self.alert_manager.export_alerts(fmt, filepath)

    def update_sniffer_config(self, config: SnifferConfig) -> bool:
        was_running = self.is_running
        if was_running:
            self.capture_engine.stop()
        self.sniffer_config = config
        self.capture_engine = CaptureEngine(config)
        if was_running:
            return self.capture_engine.start(callback=self._process_packet)
        return True

    def update_ml_config(self, config: MLModelConfig) -> bool:
        self.ml_config = config
        self.ml_engine = MLEngine(config)
        return True

    def get_correlation_analysis(self):
        return self.alert_manager.get_correlation_analysis()

    def get_signature_rule_stats(self):
        return self.signature_engine.get_rule_stats()

    def enable_signature_rule(self, rule_id: str) -> bool:
        try:
            self.signature_engine.enable_rule(rule_id)
            return True
        except Exception:
            return False

    def disable_signature_rule(self, rule_id: str) -> bool:
        try:
            self.signature_engine.disable_rule(rule_id)
            return True
        except Exception:
            return False
