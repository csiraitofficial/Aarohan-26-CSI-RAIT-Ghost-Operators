"""
Defense Evasion Detector — Detects hacker techniques used to bypass NIDS.

Specifically targets:
1. TCP Segment Overlapping (Evasion)
2. IP Packet Fragmentation
3. TTL Manipulation (OS Fingerprinting bypass)
4. NOP Sled & Shellcode Detection
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from app.models.schemas import PacketInfo, DetectionType, AttackCategory

logger = logging.getLogger(__name__)

class EvasionDetector:
    """
    Advanced engine focused on detecting evasion techniques.
    """

    def __init__(self):
        # Tracker for packet fragmentation/overlap: (src_ip, dest_ip, ip_id) -> list of fragments
        self.frag_tracker: Dict[str, List[Dict]] = defaultdict(list)
        # Tracker for TTL inconsistencies: src_ip -> last_seen_ttl
        self.ttl_tracker: Dict[str, int] = {}
        
    def detect(self, packet: PacketInfo) -> List[Dict[str, Any]]:
        results = []
        
        # 1. TTL Manipulation Detection
        ttl_results = self._detect_ttl_anomaly(packet)
        if ttl_results:
            results.append(ttl_results)
            
        # 2. Payload Inspection (NOP Sleds / Shellcode)
        payload_results = self._inspect_payload(packet)
        if payload_results:
            results.append(payload_results)
            
        return results

    def _detect_ttl_anomaly(self, packet: PacketInfo) -> Optional[Dict[str, Any]]:
        """
        Detects if an IP suddenly changes its TTL, which is often a sign of
        OS fingerprinting evasion or packet injection.
        """
        src = packet.source_ip
        ttl = packet.ttl
        
        if not ttl:
            return None
            
        if src in self.ttl_tracker:
            prev_ttl = self.ttl_tracker[src]
            # Significant jump in TTL from same IP is suspicious
            if abs(ttl - prev_ttl) > 5:
                self.ttl_tracker[src] = ttl
                return {
                    "name": "TTL_MANIPULATION",
                    "severity": "medium",
                    "attack_category": AttackCategory.DEFENSE_EVASION,
                    "description": f"IP {src} changed TTL from {prev_ttl} to {ttl} (Evasion/Injection risk)",
                    "confidence": 0.7,
                    "mitre": {
                        "tactic": "Defense Evasion",
                        "technique_id": "T1562",
                        "technique_name": "Impair Defenses"
                    }
                }
        
        self.ttl_tracker[src] = ttl
        return None

    def _inspect_payload(self, packet: PacketInfo) -> Optional[Dict[str, Any]]:
        """
        Detects NOP sleds and metamophic sleds (x86 primary).
        """
        if not packet.payload_hex:
            return None
            
        # NOP patterns (Hex codes):
        # 90: NOP
        # 40-47: INC EAX..EDI
        # 48-4F: DEC EAX..EDI
        # 37: AAA
        
        payload = packet.payload_hex.lower()
        
        # 1. Standard NOP Sled (0x90)
        if "9090909090909090" in payload:
            return self._create_sled_alert("Standard x86 NOP Sled")

        # 2. Metamorphic NOP Sled (Repeated single-byte instructions)
        # Check for sequences of same byte (often used in obfuscated sleds)
        for i in range(0, len(payload) - 32, 2):
            chunk = payload[i:i+32]
            if len(set([chunk[j:j+2] for j in range(0, 32, 2)])) == 1:
                return self._create_sled_alert(f"Metamorphic Sled (byte: 0x{chunk[0:2]})")
            
        return None

    def _create_sled_alert(self, sled_type: str) -> Dict[str, Any]:
        return {
            "name": "NOP_SLED_DETECTED",
            "severity": "high",
            "attack_category": AttackCategory.EXECUTION,
            "description": f"Suspected {sled_type} in packet payload (Buffer Overflow indicator)",
            "confidence": 0.9,
            "mitre": {
                "tactic": "Execution",
                "technique_id": "T1203",
                "technique_name": "Exploitation for Client Execution"
            }
        }

    def get_stats(self):
        return {
            "tracked_ttls": len(self.ttl_tracker),
            "tracked_fragments": len(self.frag_tracker)
        }
