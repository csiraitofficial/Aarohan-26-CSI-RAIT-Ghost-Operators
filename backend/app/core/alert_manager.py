"""
Alert Manager — handles alert creation, storage, suppression, correlation, and export.

Upgrades over original:
  - Blockchain integration is optional (pluggable via callback)
  - MITRE ATT&CK enrichment on every alert
  - Incident correlation (groups multiple alerts into incidents)
  - WebSocket broadcast callback for real-time push
"""

import json
import csv
import io
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from collections import deque
import logging
from app.blockchain.reporter import BlockchainReporter

from app.models.schemas import (
    Alert, PacketInfo, AlertSeverity, DetectionType, AttackCategory,
)
from app.db.database import db_manager
import asyncio

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages the full alert lifecycle."""

    def __init__(
        self,
        max_alerts: int = 50_000,
        alert_callback: Optional[Callable] = None,
        ws_broadcast: Optional[Callable] = None,
    ):
        self.blockchain = BlockchainReporter()
        self.max_alerts = max_alerts
        self.alert_callback = alert_callback
        self.ws_broadcast = ws_broadcast  # called with alert dict for real-time push

        self.alerts: deque = deque(maxlen=max_alerts)
        self._alert_counter = 0
        self._lock = threading.Lock()

        # Stats
        self.alerts_by_severity: Dict[str, int] = {s.value: 0 for s in AlertSeverity}
        self.alerts_by_type: Dict[str, int] = {t.value: 0 for t in DetectionType}
        self.suppressed_count = 0
        self.start_time = datetime.now()

        # Suppression
        self._suppression_cache: Dict[str, datetime] = {}
        self._suppression_ttl = timedelta(minutes=1)

        # Correlation
        self._correlations: Dict[str, Dict[str, Any]] = {}
        self._correlation_window = timedelta(minutes=5)

    # ----------------------------------------------------------------
    # Alert Creation
    # ----------------------------------------------------------------

    def create_alert(
        self,
        detection_info: Dict[str, Any],
        packet: PacketInfo,
        detection_type: DetectionType,
    ) -> Optional[Alert]:
        """Create, store, and broadcast a new alert."""
        try:
            with self._lock:
                self._alert_counter += 1
                alert_id = f"ALERT_{self._alert_counter:06d}"

            severity_raw = detection_info.get("severity", AlertSeverity.MEDIUM)
            severity = severity_raw.value if hasattr(severity_raw, "value") else str(severity_raw).lower()
            confidence = detection_info.get("confidence", 0.0)

            alert = Alert(
                id=alert_id,
                timestamp=datetime.now(),
                severity=severity,
                detection_type=detection_type,
                attack_category=detection_info.get("attack_category", AttackCategory.UNKNOWN),
                description=detection_info.get("description", "Unknown detection"),
                source_ip=packet.source_ip,
                dest_ip=packet.dest_ip,
                protocol=packet.protocol,
                source_port=packet.source_port,
                dest_port=packet.dest_port,
                confidence_score=confidence,
                packet_data={
                    "packet_length": packet.packet_length,
                    "tcp_flags": packet.tcp_flags,
                    "payload_size": packet.payload_size,
                    "detection_info": detection_info,
                },
                mitre_mapping=detection_info.get("mitre"),
            )

            self.blockchain.report_alert(
                alert.source_ip,
                alert.attack_category.value if hasattr(alert.attack_category, 'value') else str(alert.attack_category)
            )
            # Store & Stats (Thread-safe)
            with self._lock:
                # Suppression
                if self._should_suppress(alert):
                    self.suppressed_count += 1
                    return None

                self.alerts.append(alert)
                self.alerts_by_severity[severity] = self.alerts_by_severity.get(severity, 0) + 1
                self.alerts_by_type[detection_type.value] = self.alerts_by_type.get(detection_type.value, 0) + 1

            # Persist to Database (Async)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(db_manager.insert_alert(alert.model_dump()))
            except Exception as e:
                logger.error(f"Failed to persist alert to DB: {e}")

            # Correlate
            self._correlate(alert)

            # Callbacks
            if self.alert_callback:
                try:
                    self.alert_callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

            # WebSocket broadcast
            if self.ws_broadcast:
                try:
                    self.ws_broadcast(alert.model_dump(mode="json"))
                except Exception:
                    pass

            logger.info(f"Alert {alert_id}: {alert.description} [{severity}]")
            return alert

        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None

    def create_ml_alert(self, ml_info: Dict[str, Any], packet: PacketInfo) -> Optional[Alert]:
        if not ml_info.get("is_anomalous", False):
            return None
        if ml_info.get("confidence", 0) < 0.3:
            return None
        return self.create_alert(ml_info, packet, DetectionType.ML)

    def create_signature_alert(self, sig_info: Dict[str, Any], packet: PacketInfo) -> Optional[Alert]:
        return self.create_alert(sig_info, packet, DetectionType.SIGNATURE)

    def create_hybrid_alert(
        self, ml_info: Dict[str, Any], sig_info: Dict[str, Any], packet: PacketInfo,
    ) -> Optional[Alert]:
        severity_order = {s.value: i for i, s in enumerate(AlertSeverity)}
        ml_sev = ml_info.get("severity", AlertSeverity.LOW)
        sig_sev = sig_info.get("severity", AlertSeverity.LOW)
        ml_val = ml_sev.value if hasattr(ml_sev, "value") else str(ml_sev)
        sig_val = sig_sev.value if hasattr(sig_sev, "value") else str(sig_sev)
        combined_sev = ml_val if severity_order.get(ml_val, 0) >= severity_order.get(sig_val, 0) else sig_val

        combined = {
            "severity": combined_sev,
            "description": f"Hybrid: {ml_info.get('description', '')} + {sig_info.get('description', '')}",
            "confidence": max(ml_info.get("confidence", 0), sig_info.get("confidence", 0)),
            "attack_category": sig_info.get("attack_category", AttackCategory.UNKNOWN),
        }
        return self.create_alert(combined, packet, DetectionType.HYBRID)

    # ----------------------------------------------------------------
    # Query
    # ----------------------------------------------------------------

    def get_alerts(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
        detection_type: Optional[DetectionType] = None,
        source_ip: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[Alert]:
        alerts = list(self.alerts)
        if severity:
            alerts = [a for a in alerts if a.severity == severity.value or a.severity == severity]
        if detection_type:
            alerts = [a for a in alerts if a.detection_type == detection_type]
        if source_ip:
            alerts = [a for a in alerts if a.source_ip == source_ip]
        if resolved is not None:
            alerts = [a for a in alerts if a.is_resolved == resolved]
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return alerts[:limit]

    def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        for a in self.alerts:
            if a.id == alert_id:
                return a
        return None

    # ----------------------------------------------------------------
    # Resolution
    # ----------------------------------------------------------------

    def resolve_alert(self, alert_id: str, resolved_by: str = "", notes: str = "") -> bool:
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            return False
        alert.is_resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.now()
        alert.resolution_notes = notes
        return True

    def delete_alert(self, alert_id: str) -> bool:
        with self._lock:
            for i, a in enumerate(self.alerts):
                if a.id == alert_id:
                    del self.alerts[i]
                    return True
        return False

    def clear_alerts(self, older_than: Optional[timedelta] = None):
        if older_than:
            cutoff = datetime.now() - older_than
            with self._lock:
                self.alerts = deque(
                    [a for a in self.alerts if a.timestamp > cutoff],
                    maxlen=self.max_alerts,
                )
        else:
            with self._lock:
                self.alerts.clear()
            self.alerts_by_severity = {s.value: 0 for s in AlertSeverity}
            self.alerts_by_type = {t.value: 0 for t in DetectionType}

    # ----------------------------------------------------------------
    # Export
    # ----------------------------------------------------------------

    def export_alerts(self, fmt: str = "json", filepath: Optional[str] = None) -> str:
        data = []
        for a in self.alerts:
            data.append({
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "severity": a.severity if isinstance(a.severity, str) else a.severity.value,
                "detection_type": a.detection_type.value,
                "description": a.description,
                "source_ip": a.source_ip,
                "dest_ip": a.dest_ip,
                "protocol": a.protocol,
                "confidence_score": a.confidence_score,
                "is_resolved": a.is_resolved,
            })

        if fmt == "csv":
            buf = io.StringIO()
            if data:
                w = csv.DictWriter(buf, fieldnames=data[0].keys())
                w.writeheader()
                w.writerows(data)
            output = buf.getvalue()
        else:
            output = json.dumps(data, indent=2)

        if filepath:
            with open(filepath, "w") as f:
                f.write(output)
        return output

    # ----------------------------------------------------------------
    # Stats & Correlation
    # ----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_alerts": len(self.alerts),
            "alerts_by_severity": dict(self.alerts_by_severity),
            "alerts_by_type": dict(self.alerts_by_type),
            "resolved_alerts": sum(1 for a in self.alerts if a.is_resolved),
            "suppressed_alerts": self.suppressed_count,
            "correlated_groups": len(self._correlations),
            "uptime_seconds": uptime,
            "alert_rate_per_minute": len(self.alerts) / max(uptime / 60, 1),
        }

    def get_correlation_analysis(self) -> Dict[str, Any]:
        correlations = []
        for key, info in self._correlations.items():
            correlations.append({
                "source_ip": info["source_ip"],
                "alert_count": info["count"],
                "first_seen": info["first_seen"].isoformat(),
                "last_seen": info["last_seen"].isoformat(),
            })
        return {"total_correlations": len(correlations), "correlations": correlations}

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    def _should_suppress(self, alert: Alert) -> bool:
        key = f"{alert.source_ip}_{alert.description}"
        now = datetime.now()
        if key in self._suppression_cache:
            if now - self._suppression_cache[key] < self._suppression_ttl:
                return True
        self._suppression_cache[key] = now
        # Evict old entries
        cutoff = now - timedelta(minutes=5)
        self._suppression_cache = {k: v for k, v in self._suppression_cache.items() if v > cutoff}
        return False

    def _correlate(self, alert: Alert):
        key = f"src_{alert.source_ip}"
        if key not in self._correlations:
            self._correlations[key] = {
                "source_ip": alert.source_ip, "count": 0,
                "first_seen": alert.timestamp, "last_seen": alert.timestamp,
            }
        c = self._correlations[key]
        c["count"] += 1
        c["last_seen"] = alert.timestamp

        if c["count"] >= 5:
            logger.warning(f"Correlation: {c['count']} alerts from {alert.source_ip}")

        # Evict old correlations
        cutoff = datetime.now() - self._correlation_window
        self._correlations = {k: v for k, v in self._correlations.items() if v["last_seen"] > cutoff}
