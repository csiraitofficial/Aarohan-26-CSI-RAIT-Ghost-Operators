"""
Advanced Signature Detection Engine

Upgrades over original SignatureDetector:
  - MITRE ATT&CK tactic/technique mapping for every rule
  - Configurable ConnectionTracker with sliding window
  - Ready for Suricata / Snort rule format parsing (Phase 2)
  - Enhanced detection: DNS tunneling, data exfiltration, C2 beaconing
"""

import re
import time
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Deque, Tuple
from collections import defaultdict, deque, namedtuple
import logging

from app.detection.suricata_parser import SuricataParser, SuricataRule
from app.models.schemas import (
    PacketInfo, AlertSeverity, DetectionType,
    AttackCategory, MITREMapping,
)

logger = logging.getLogger(__name__)

Connection = namedtuple("Connection", ["src_ip", "dst_ip", "dst_port", "timestamp", "packet_count"])


# ============================================================
# Connection Tracker
# ============================================================

class ConnectionTracker:
    """Stateful tracker for network connections within a sliding window."""

    def __init__(self, window_seconds: int = 300, max_track_size: int = 10000):
        self.window = window_seconds
        self.max_track_size = max_track_size
        self._connections: Deque[Connection] = deque(maxlen=max_track_size)
        self._syn_counts: Dict[str, int] = defaultdict(int)
        self._port_access: Dict[str, Set[int]] = defaultdict(set)
        self._src_packet_counts: Dict[str, int] = defaultdict(int)
        self._failed_auths: Dict[str, int] = defaultdict(int)
        self._protocol_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._last_cleanup = time.time()

    def update(self, packet: PacketInfo):
        """Track a new packet with resource limits."""
        now = datetime.now()
        
        # Resource exhaustion prevention
        if len(self._syn_counts) > 5000: # Limit tracked source IPs
            self._cleanup_all()

        conn = Connection(
            src_ip=packet.source_ip,
            dst_ip=packet.dest_ip,
            dst_port=packet.dest_port or 0,
            timestamp=now,
            packet_count=1,
        )
        self._connections.append(conn)
        self._src_packet_counts[packet.source_ip] += 1
        self._protocol_counts[packet.source_ip][packet.protocol] += 1

        if packet.dest_port:
            port_set = self._port_access[packet.source_ip]
            if len(port_set) < 1000: # Limit ports per IP
                port_set.add(packet.dest_port)

        if packet.tcp_flags and "SYN" in packet.tcp_flags:
            self._syn_counts[packet.source_ip] += 1

        # Periodic cleanup
        if time.time() - self._last_cleanup > 30:
            self._cleanup()
            self._last_cleanup = time.time()

    def _cleanup(self):
        cutoff = datetime.now() - timedelta(seconds=self.window)
        while self._connections and self._connections[0].timestamp < cutoff:
            old = self._connections.popleft()
            self._src_packet_counts[old.src_ip] = max(0, self._src_packet_counts[old.src_ip] - 1)

    def get_unique_ports_count(self, src_ip: str) -> int:
        return len(self._port_access.get(src_ip, set()))

    def get_syn_count(self, src_ip: str) -> int:
        return self._syn_counts.get(src_ip, 0)

    def get_packet_rate(self, src_ip: str) -> float:
        count = self._src_packet_counts.get(src_ip, 0)
        return count / max(self.window, 1)

    def get_source_ips_for_port(self, dst_port: int) -> int:
        return sum(
            1 for conn in self._connections
            if conn.dst_port == dst_port
        )

    def record_failed_auth(self, src_ip: str, dst_ip: str):
        key = f"{src_ip}->{dst_ip}"
        self._failed_auths[key] += 1

    def get_failed_auths(self, src_ip: str, dst_ip: str) -> int:
        return self._failed_auths.get(f"{src_ip}->{dst_ip}", 0)


# ============================================================
# Signature Rule
# ============================================================

class SignatureRule:
    """A single signature-based detection rule with MITRE mapping."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        pattern: str,
        severity: AlertSeverity,
        description: str,
        attack_category: AttackCategory = AttackCategory.UNKNOWN,
        mitre: Optional[MITREMapping] = None,
        enabled: bool = True,
        tags: Optional[List[str]] = None,
    ):
        self.rule_id = rule_id
        self.name = name
        self.pattern = pattern
        self.severity = severity
        self.description = description
        self.attack_category = attack_category
        self.mitre = mitre
        self.enabled = enabled
        self.tags = tags or []
        self.match_count = 0
        self.last_match: Optional[datetime] = None

        self._compiled = None
        self._compile_pattern()

    def _compile_pattern(self):
        try:
            if self.pattern.startswith("regex:"):
                self._compiled = re.compile(self.pattern[6:], re.IGNORECASE)
            elif self.pattern.startswith("port_range:"):
                parts = self.pattern[11:].split("-")
                self._compiled = (int(parts[0]), int(parts[1]))
            else:
                self._compiled = re.compile(re.escape(self.pattern), re.IGNORECASE)
        except Exception as e:
            logger.warning(f"Rule {self.rule_id}: pattern compile error: {e}")
            self._compiled = None

    def match(self, packet: PacketInfo, tracker: Optional[ConnectionTracker] = None) -> bool:
        """Check whether the packet matches this rule."""
        if not self.enabled or self._compiled is None:
            return False

        try:
            # Port-scan detection
            if self.rule_id.startswith("PORT_SCAN") and tracker:
                return self._detect_port_scan(packet, tracker)

            # DDoS detection
            if self.rule_id.startswith("DDOS") and tracker:
                return self._detect_ddos(packet, tracker)

            # Brute-force detection
            if self.rule_id.startswith("BRUTE_FORCE") and tracker:
                return self._detect_brute_force(packet, tracker)

            # Port-range matching
            if isinstance(self._compiled, tuple):
                lo, hi = self._compiled
                port = packet.dest_port or 0
                return lo <= port <= hi

            # Regex payload matching
            if packet.payload_hex:
                try:
                    payload_text = bytes.fromhex(packet.payload_hex).decode("utf-8", errors="ignore")
                    if self._compiled.search(payload_text):
                        return True
                except Exception:
                    pass

            # Header-level regex
            header_str = f"{packet.source_ip} {packet.dest_ip} {packet.protocol} {packet.tcp_flags or ''}"
            return bool(self._compiled.search(header_str))

        except Exception as e:
            logger.debug(f"Rule {self.rule_id} match error: {e}")
            return False

    # ---- Stateful detectors ----

    def _detect_port_scan(self, pkt: PacketInfo, tracker: ConnectionTracker) -> bool:
        unique_ports = tracker.get_unique_ports_count(pkt.source_ip)
        syn_count = tracker.get_syn_count(pkt.source_ip)
        return unique_ports > 15 or syn_count > 50

    def _detect_ddos(self, pkt: PacketInfo, tracker: ConnectionTracker) -> bool:
        rate = tracker.get_packet_rate(pkt.source_ip)
        return rate > 100  # > 100 pps from a single source

    def _detect_brute_force(self, pkt: PacketInfo, tracker: ConnectionTracker) -> bool:
        failed = tracker.get_failed_auths(pkt.source_ip, pkt.dest_ip)
        return failed >= 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "severity": self.severity.value,
            "description": self.description,
            "attack_category": self.attack_category.value,
            "enabled": self.enabled,
            "tags": self.tags,
            "match_count": self.match_count,
            "last_match": self.last_match.isoformat() if self.last_match else None,
            "mitre": self.mitre.model_dump() if self.mitre else None,
        }


# ============================================================
# Signature Engine
# ============================================================

class SignatureEngine:
    """Manages signature rules and performs stateful detection."""

    def __init__(self):
        self.rules: List[SignatureRule] = []
        self.suricata_parser = SuricataParser()
        self.connection_tracker = ConnectionTracker()
        self.total_matches = 0
        self._load_default_rules()
        self._load_suricata_rules()

    def _load_suricata_rules(self):
        # Placeholder for loading from a file in future
        pass

    # ----------------------------------------------------------------
    # Rule Management
    # ----------------------------------------------------------------

    def _load_default_rules(self):
        """Load a comprehensive set of default detection rules."""
        rules_spec = [
            # Port Scanning
            ("PORT_SCAN_001", "TCP Port Scan", "regex:.*", AlertSeverity.HIGH,
             "Detected port scanning activity from source IP",
             AttackCategory.RECONNAISSANCE,
             MITREMapping(tactic="Reconnaissance", technique_id="T1046", technique_name="Network Service Scanning")),

            # DDoS
            ("DDOS_001", "SYN Flood", "regex:.*SYN.*", AlertSeverity.CRITICAL,
             "Detected SYN flood / DDoS attack pattern",
             AttackCategory.IMPACT,
             MITREMapping(tactic="Impact", technique_id="T1498", technique_name="Network Denial of Service")),

            # Brute Force
            ("BRUTE_FORCE_001", "SSH Brute Force", "port_range:22-22", AlertSeverity.HIGH,
             "Detected brute-force authentication attempts on SSH",
             AttackCategory.CREDENTIAL_ACCESS,
             MITREMapping(tactic="Credential Access", technique_id="T1110", technique_name="Brute Force")),

            ("BRUTE_FORCE_002", "RDP Brute Force", "port_range:3389-3389", AlertSeverity.HIGH,
             "Detected brute-force authentication attempts on RDP",
             AttackCategory.CREDENTIAL_ACCESS,
             MITREMapping(tactic="Credential Access", technique_id="T1110", technique_name="Brute Force")),

            # SQL Injection
            ("SQLI_001", "SQL Injection Attempt",
             "regex:(SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\\s",
             AlertSeverity.CRITICAL,
             "Detected SQL injection attempt in payload",
             AttackCategory.INITIAL_ACCESS,
             MITREMapping(tactic="Initial Access", technique_id="T1190", technique_name="Exploit Public-Facing Application")),

            # XSS
            ("XSS_001", "Cross-Site Scripting",
             "regex:<script|javascript:|onerror|onload|eval\\(",
             AlertSeverity.HIGH,
             "Detected XSS payload in network traffic",
             AttackCategory.INITIAL_ACCESS,
             MITREMapping(tactic="Initial Access", technique_id="T1189", technique_name="Drive-by Compromise")),

            # Command Injection
            ("CMD_INJ_001", "Command Injection",
             "regex:(;|\\||&&)\\s*(cat|ls|pwd|whoami|id|wget|curl|nc|bash|sh|python)\\s",
             AlertSeverity.CRITICAL,
             "Detected OS command injection attempt",
             AttackCategory.EXECUTION,
             MITREMapping(tactic="Execution", technique_id="T1059", technique_name="Command and Scripting Interpreter")),

            # Directory Traversal
            ("DIR_TRAV_001", "Directory Traversal",
             "regex:\\.\\./|\\.\\.\\\\",
             AlertSeverity.HIGH,
             "Detected directory traversal attempt",
             AttackCategory.DISCOVERY,
             MITREMapping(tactic="Discovery", technique_id="T1083", technique_name="File and Directory Discovery")),

            # Suspicious Ports
            ("SUSP_PORT_001", "IRC Traffic", "port_range:6660-6669", AlertSeverity.MEDIUM,
             "IRC traffic detected — potential C2 channel",
             AttackCategory.COMMAND_AND_CONTROL,
             MITREMapping(tactic="Command and Control", technique_id="T1071", technique_name="Application Layer Protocol")),

            # DNS Tunneling Indicator
            ("DNS_TUN_001", "DNS Tunneling Suspect", "port_range:53-53", AlertSeverity.MEDIUM,
             "High-volume DNS traffic — potential DNS tunneling",
             AttackCategory.COMMAND_AND_CONTROL,
             MITREMapping(tactic="Command and Control", technique_id="T1071.004", technique_name="DNS")),

            # Large Data Transfer (potential exfiltration)
            ("EXFIL_001", "Large Outbound Transfer",
             "regex:.*", AlertSeverity.MEDIUM,
             "Large outbound data transfer detected",
             AttackCategory.EXFILTRATION,
             MITREMapping(tactic="Exfiltration", technique_id="T1048", technique_name="Exfiltration Over Alternative Protocol")),

            # Telnet
            ("TELNET_001", "Telnet Access", "port_range:23-23", AlertSeverity.MEDIUM,
             "Telnet connection detected — unencrypted protocol",
             AttackCategory.INITIAL_ACCESS,
             MITREMapping(tactic="Initial Access", technique_id="T1021", technique_name="Remote Services")),

            # Elite: DNS Tunneling (Sophisticated)
            ("DNS_TUNNEL_ELITE", "Advanced DNS Tunneling", "regex:(?i)[a-z0-9]{20,}\\.com", AlertSeverity.HIGH,
             "Detected long, high-entropy DNS query — likely C2 tunneling",
             AttackCategory.COMMAND_AND_CONTROL,
             MITREMapping(tactic="Command and Control", technique_id="T1071.004", technique_name="DNS")),

            # Elite: SMB Enumeration
            ("SMB_ENUM_ELITE", "SMB Session Enumeration", "port_range:445-445", AlertSeverity.HIGH,
             "Detected suspicious SMB session enumeration / lateral movement",
             AttackCategory.LATERAL_MOVEMENT,
             MITREMapping(tactic="Lateral Movement", technique_id="T1021.002", technique_name="SMB/Windows Admin Shares")),

            # Elite: RDP Tunneling (SSH/VPN)
            ("RDP_TUNNEL_ELITE", "RDP Over Non-Standard Port", "regex:.*RDP.*", AlertSeverity.HIGH,
             "Detected RDP protocol signature on non-standard port",
             AttackCategory.COMMAND_AND_CONTROL,
             MITREMapping(tactic="Command and Control", technique_id="T1571", technique_name="Non-Standard Port")),
        ]

        for spec in rules_spec:
            rule = SignatureRule(
                rule_id=spec[0], name=spec[1], pattern=spec[2],
                severity=spec[3], description=spec[4],
                attack_category=spec[5], mitre=spec[6],
            )
            self.rules.append(rule)

        logger.info(f"Loaded {len(self.rules)} signature rules")

    # ----------------------------------------------------------------
    # Detection
    # ----------------------------------------------------------------

    def detect(self, packet: PacketInfo) -> List[Dict[str, Any]]:
        """Run all enabled rules against the packet."""
        self.connection_tracker.update(packet)
        detections = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Special handling: exfiltration check needs large payload
            if rule.rule_id == "EXFIL_001":
                if packet.payload_size < 10_000:
                    continue

            if rule.match(packet, self.connection_tracker):
                rule.match_count += 1
                rule.last_match = datetime.now()
                self.total_matches += 1

                detection = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity,
                    "description": rule.description,
                    "detection_type": DetectionType.SIGNATURE,
                    "attack_category": rule.attack_category,
                    "confidence": 0.9,
                    "tags": rule.tags,
                }
                if rule.mitre:
                    detection["mitre"] = rule.mitre.model_dump()

                detections.append(detection)

        return detections

    # ----------------------------------------------------------------
    # Rule Management API
    # ----------------------------------------------------------------

    def enable_rule(self, rule_id: str):
        for r in self.rules:
            if r.rule_id == rule_id:
                r.enabled = True
                return
        raise ValueError(f"Rule {rule_id} not found")

    def disable_rule(self, rule_id: str):
        for r in self.rules:
            if r.rule_id == rule_id:
                r.enabled = False
                return
        raise ValueError(f"Rule {rule_id} not found")

    def get_rule_stats(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.rules]

    def get_stats(self) -> Dict[str, Any]:
        enabled = sum(1 for r in self.rules if r.enabled)
        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled,
            "disabled_rules": len(self.rules) - enabled,
            "total_matches": self.total_matches,
            "rules_by_severity": {
                sev.value: sum(1 for r in self.rules if r.severity == sev and r.enabled)
                for sev in AlertSeverity
            },
        }
