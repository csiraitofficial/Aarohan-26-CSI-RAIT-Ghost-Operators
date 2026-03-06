"""
Honeypot — Deception and analysis module.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HoneypotManager:
    """
    Manages deception services. In this local version, it mainly 
    acts as a 'Ghost Service' that logs all attempts to access invalid ports.
    """

    def __init__(self):
        self.lured_ips: Dict[str, int] = {} # ip -> hit_count
        self.interaction_log: List[Dict[str, Any]] = []

    def log_interaction(self, ip: str, port: int, payload: str = ""):
        """Logs an attempt to interact with a honeypot/ghost port."""
        self.lured_ips[ip] = self.lured_ips.get(ip, 0) + 1
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "port": port,
            "payload_preview": payload[:50] if payload else "N/A"
        }
        self.interaction_log.append(entry)
        logger.info(f"HONEYPOT HIT: {ip} tried port {port}")

        if len(self.interaction_log) > 500:
            self.interaction_log.pop(0)

    def get_stats(self):
        return {
            "total_hits": len(self.interaction_log),
            "unique_attackers": len(self.lured_ips),
            "top_attackers": sorted(self.lured_ips.items(), key=lambda x: x[1], reverse=True)[:5]
        }
