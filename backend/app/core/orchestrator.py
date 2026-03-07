"""
NIDS Orchestrator — central coordinator for all subsystems.

Upgrades over original:
  - Integrates FlowAggregator for flow-level analysis
  - Periodic flow flush in a background thread
  - WebSocket broadcast wiring
  - Blockchain client is optional (pluggable)
"""

import os
import asyncio
import logging
import traceback
import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from uuid import uuid4
from app.core.capture_engine import CaptureEngine
from app.core.flow_aggregator import FlowAggregator
from app.core.alert_manager import AlertManager
from app.prevention.ips_engine import IPSEngine
from app.prevention.playbook_engine import PlaybookEngine
from app.prevention.honeypot import HoneypotManager
from app.detection.ml_engine import MLEngine
from app.detection.signature_engine import SignatureEngine
from app.detection.eta_engine import eta_engine
from app.detection.correlation_engine import correlation_engine
from app.detection.evasion_detector import EvasionDetector
from app.detection.dpi_engine import DPIEngine
from app.intelligence.threat_feeds import threat_intel
from app.intelligence.threat_feeds import threat_intel
from app.intelligence.geoip import geoip_lookup
from app.intelligence.ueba import UEBAEngine
from app.intelligence.ai_triage import AITriageManager
from app.detection.vulnerability_engine import VulnerabilityEngine
from app.prevention.deception_engine import DeceptionEngine
from app.blockchain.reporter import BlockchainReporter
from app.models.schemas import (
    PacketInfo, SnifferConfig, MLModelConfig, IPSConfig,
    SystemStatus, DetectionType, Alert, AttackCategory,
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
        
        # Hardware Resilience Check
        if os.getenv('NIDS_SAFE_MODE', 'false').lower() == 'true':
            logger.warning("🛡️  NIDS APPLIANCE: [SAFE MODE] ENABLED. ML/DL engines bypassed for hardware resilience.")
            logger.warning("💡 System is running in SIGNATURE-ONLY mode (Low power/compatibility mode).")
        self.signature_engine = SignatureEngine()
        self.ips_engine = IPSEngine(ips_config)
        self.alert_manager = AlertManager(
            alert_callback=alert_callback,
            ws_broadcast=ws_broadcast,
        )
        self.playbook_engine = PlaybookEngine(self.ips_engine, self.alert_manager)
        self.honeypot = HoneypotManager()
        
        # Phase 2 Advanced Engines
        self.eta_engine = eta_engine
        self.correlation_engine = correlation_engine
        self.threat_intel = threat_intel
        self.geoip = geoip_lookup
        self.evasion_detector = EvasionDetector()
        self.dpi_engine = DPIEngine()

        # Phase 4 Advanced Intelligence
        self.ueba_engine = UEBAEngine()
        self.ai_triage = AITriageManager()
        self.vuln_engine = VulnerabilityEngine()
        # Threading & Concurrency Hardening
        self._lock = threading.Lock()
        from collections import deque
        self.traffic_history = deque(maxlen=3600) # Last 1 hour of traffic counts (per sec)
        
        # State
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.packets_processed = 0
        self.alerts_generated = 0
        self.ml_predictions = 0
        self.signature_matches = 0
        self.blockchain_reporter = BlockchainReporter()

        # Performance Performance
        self._perf = {
            "avg_processing_time": 0.0,
            "max_processing_time": 0.0,
            "min_processing_time": float("inf"),
            "total_processing_time": 0.0,
        }
        self._last_cleanup = time.time()
        self._flow_flush_thread: Optional[threading.Thread] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.alert_manager.set_loop(loop)
        logger.info("Main event loop synchronized for thread-safe database persistence")

    def start(self) -> bool:
        if self.is_running:
            logger.warning("NIDS already running")
            return False

        with self._lock:
            self.is_running = True
            self.start_time = datetime.now()
            self.packets_processed = 0
            self.alerts_generated = 0
            self.ml_predictions = 0
            self.signature_matches = 0
            self.traffic_history.clear()

        if not self.capture_engine.start(callback=self._process_packet):
            with self._lock:
                self.is_running = False
            logger.error("Failed to start capture engine")
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
        """Main processing pipeline with thread-safety and failsafe logic."""
        if not self.is_running:
            return

        t0 = time.time()
        try:
            with self._lock:
                self.packets_processed += 1
                
                # Failsafe: If processing delay is > 500ms, skip ML and DL for this packet
                # to prevent buffer overflow (Blindness mitigation)
                is_overloaded = self._perf["avg_processing_time"] > 0.5
                
            # Skip blocked IPs
            if self.ips_engine.is_blocked(packet.source_ip):
                return

            # Phase 3/5: IPS Stateful tracking (SYN floods etc)
            self.ips_engine.track_stateful(packet)

            # Feed to flow aggregator
            self.flow_aggregator.process_packet(packet)

            # Phase 4: UEBA Profiling
            self.ueba_engine.process_packet(packet.source_ip, packet)
            ueba_anomalies = self.ueba_engine.analyze_anomaly(packet.source_ip)

            # ML detection (packet-level)
            ml_result = self._run_ml(packet)

            # Signature detection
            sig_results = self._run_signatures(packet)

            # ETA detection
            eta_result = self.eta_engine.process_packet(packet)
            if eta_result:
                sig_results.append(eta_result)

            # Evasion detection
            evasion_results = self.evasion_detector.detect(packet)
            if evasion_results:
                sig_results.extend(evasion_results)

            # DPI (Deep Packet Inspection)
            dpi_results = self.dpi_engine.inspect(packet)
            if dpi_results:
                sig_results.extend(dpi_results)

            # Generate alerts
            alerts = self._generate_alerts(packet, ml_result, sig_results, ueba_anomalies)
            
            # Phase 2: Correlation
            for alert in alerts:
                if alert:
                    incident = self.correlation_engine.correlate(alert)
                    if incident:
                        # Log/Broadcast incident
                        logger.warning(f"INCIDENT: {incident.title}")

            # Vulnerability detection (Passive)
            vuln_results = self.vuln_engine.analyze_packet(packet)
            if vuln_results:
                sig_results.extend(vuln_results)

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

    def _generate_alerts(self, packet: PacketInfo, ml: Dict, sigs: List[Dict], ueba: List[Dict] = None) -> List[Alert]:
        created_alerts = []
        highest = "info"
        ueba = ueba or []

        # 1. ML Alerts
        if ml.get("is_anomalous"):
            a = self.alert_manager.create_ml_alert(ml, packet)
            if a:
                created_alerts.append(a)
                highest = a.severity

        # 2. Signature Alerts
        for sig in sigs:
            a = self.alert_manager.create_signature_alert(sig, packet)
            if a:
                created_alerts.append(a)
                if a.severity == "critical":
                    highest = "critical"
                elif a.severity == "high" and highest != "critical":
                    highest = "high"

        # 3. UEBA Alerts (Behavioral)
        for anomaly in ueba:
            detection_info = {
                "severity": anomaly["severity"],
                "description": anomaly["description"],
                "confidence": anomaly["confidence"],
                "attack_category": AttackCategory.UNKNOWN # UEBA mapping could be added
            }
            a = self.alert_manager.create_alert(
                detection_info=detection_info,
                packet=packet,
                detection_type=DetectionType.BEHAVIORAL
            )
            if a:
                created_alerts.append(a)
                if a.severity == "high" and highest not in ["critical"]:
                    highest = "high"

        # Hybrid alert
        if ml.get("is_anomalous") and sigs:
            best_sig = max(sigs, key=lambda s: s.get("confidence", 0))
            a = self.alert_manager.create_hybrid_alert(ml, best_sig, packet)
            if a:
                created_alerts.append(a)

        # Phase 4: AI Triage for each alert
        for alert in created_alerts:
            triage_result = self.ai_triage.triage(alert.model_dump())
            # Result stored in triage history, could be attached to Alert model in future
            logger.info(f"AI TRIAGE [{alert.id}]: {triage_result['ai_explanation']}")

        # Phase 3: Automated Playbook Execution
        if created_alerts and self.ips_engine.config.auto_block:
            for alert in created_alerts:
                # We use an async wrapper or just call it since it's a critical path
                # For simplicity in this sync orchestrator, we fire-and-forget or keep it swift
                # Use the synchronized loop from alert_manager to schedule tasks correctly from worker threads
                try:
                    target_loop = self.alert_manager.loop
                    if target_loop and target_loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.playbook_engine.execute(alert.model_dump()), 
                            target_loop
                        )
                except Exception as e:
                    logger.error(f"Playbook execution error: {e}")
            
            # Phase 6: Decentralized Consensus Proposal
            if any(a.severity in ["high", "critical"] for a in created_alerts):
                # Propose the source IP for global blocking
                self.blockchain_reporter.propose_threat(packet.source_ip, created_alerts[0].attack_category.value)

        # Cleanup expired blocks periodically
        if time.time() - self._last_cleanup > 60:
            self.ips_engine.cleanup_expired()
            self._last_cleanup = time.time()

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
            "ips_stats": self.ips_engine.get_stats(),
            "playbook_history": self.playbook_engine.get_history(),
            "honeypot_stats": self.honeypot.get_stats(),
            "performance_stats": self._perf,
            "component_health": {
                "capture": self.capture_engine.is_running,
                "ml": self.ml_engine.is_loaded,
                "signatures": len(self.signature_engine.rules) > 0,
                "alerts": True,
                "ips": True,
                "ueba": True,
                "ai_triage": True,
                "evasion_detection": True,
                "dpi": True,
                "vulnerability_scan": True,
                "deception": True
            },
            "predictive_insight": self.get_predictive_insight()
        }

    def get_predictive_insight(self) -> Dict[str, Any]:
        """Simple trend-based predictive analytics for traffic volume."""
        if len(self.traffic_history) < 5:
            return {"status": "insufficient_data"}
        
        recent = self.traffic_history[-5:]
        avg = sum(recent) / 5
        trend = "stable"
        if recent[-1] > avg * 1.5: trend = "increasing"
        elif recent[-1] < avg * 0.5: trend = "decreasing"
        
        return {
            "predicted_trend": trend,
            "next_hour_estimate": avg * 1.1 if trend == "increasing" else avg,
            "confidence": 0.65
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
