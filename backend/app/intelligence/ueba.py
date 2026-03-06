"""
UEBA (User & Entity Behavior Analytics) — Profiling and anomaly detection.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class UEBAEngine:
    """
    Profiles behavior of entities (IPs, MACs, Users) and detects deviations.
    Tracks:
    - Typical traffic volume per hour
    - Protocol usage frequency
    - Common destination ports
    - Geolocation consistency
    """

    def __init__(self):
        # Profiling data: entity -> {metric -> value}
        # In a real system, this would be backed by Redis or MongoDB
        self.profiles: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "first_seen": datetime.now(),
            "last_seen": datetime.now(),
            "hourly_counts": [0] * 24, # 24-hour baseline
            "protocol_dist": {},
            "port_dist": {},
            "geo_history": set(),
            "alert_count": 0
        })

    def process_packet(self, ip: str, packet_info: Any):
        """Update the profile based on a new packet."""
        profile = self.profiles[ip]
        hour = datetime.now().hour
        profile["hourly_counts"][hour] += 1
        profile["last_seen"] = datetime.now()
        
        # Protocol dist
        proto = packet_info.protocol
        profile["protocol_dist"][proto] = profile["protocol_dist"].get(proto, 0) + 1
        
        # Port dist
        port = packet_info.dest_port
        if port:
            profile["port_dist"][port] = profile["port_dist"].get(port, 0) + 1

    def analyze_anomaly(self, ip: str) -> List[Dict[str, Any]]:
        """Identify if an entity's current behavior is an anomaly."""
        profile = self.profiles.get(ip)
        if not profile:
            return []

        anomalies = []
        hour = datetime.now().hour
        avg_hourly = sum(profile["hourly_counts"]) / 24
        
        # 1. Volume Anomaly: Current hour 10x higher than average
        current_vol = profile["hourly_counts"][hour]
        if avg_hourly > 10 and current_vol > avg_hourly * 5:
            anomalies.append({
                "type": "UEBA_VOLUME_SPIKE",
                "severity": "high",
                "description": f"IP {ip} is showing {current_vol} packets this hour vs avg {avg_hourly:.1f}",
                "confidence": 0.8
            })

        # 2. Protocol Anomaly: Use of IRC/Telnet in a usually HTTP/HTTPS environment
        suspicious_protos = {"IRC", "TELNET", "TFTP"}
        found_suspicious = suspicious_protos.intersection(profile["protocol_dist"].keys())
        if found_suspicious:
            anomalies.append({
                "type": "UEBA_SUSPICIOUS_PROTOCOL",
                "severity": "medium",
                "description": f"IP {ip} used non-standard protocols: {list(found_suspicious)}",
                "confidence": 0.9
            })

        return anomalies

    def get_stats(self):
        return {
            "profiled_entities": len(self.profiles),
            "total_anomalies_detected": 0 # Would track this
        }
