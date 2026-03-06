"""
Playbook Engine — Automated context-aware response flows.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PlaybookEngine:
    """
    Executes automated response playbooks based on alert severity and type.
    Example: 
    If 'DDoS' alert comes from 'External' IP with 'High' confidence:
    1. Block IP for 2 hours.
    2. Notify Admin via WebSocket.
    3. Log to Blockchain.
    """

    def __init__(self, ips_engine: Any, alert_manager: Any):
        self.ips = ips_engine
        self.alert_manager = alert_manager
        self.execution_history: List[Dict[str, Any]] = []

    async def execute(self, alert_data: Dict[str, Any]):
        """Runs the appropriate playbook for the given alert."""
        severity = alert_data.get("severity", "info")
        alert_type = alert_data.get("type", "unknown")
        ip = alert_data.get("source_ip")

        if not ip:
            return

        # Playbook 1: Critical Intrusion
        if severity == "critical":
            await self._critical_intrusion_playbook(ip, alert_data)
        
        # Playbook 2: Brute Force Detection
        elif "brute_force" in alert_type.lower():
            await self._brute_force_playbook(ip, alert_data)

        # Playbook 3: Anomaly Detected
        elif severity == "high":
            await self._high_alert_playbook(ip, alert_data)

    async def _critical_intrusion_playbook(self, ip: str, alert: Dict):
        logger.warning(f"PLAYBOOK [Critical]: Hard blocking {ip}")
        self.ips.block_ip(ip, duration_minutes=1440, reason=f"Critical Alert: {alert.get('name')}")
        self._record_action("Critical Block", ip, alert.get("id"))

    async def _brute_force_playbook(self, ip: str, alert: Dict):
        logger.info(f"PLAYBOOK [Brute Force]: Temporary block for {ip}")
        self.ips.block_ip(ip, duration_minutes=30, reason="Repeated authentication failure")
        self._record_action("Brute Force Block", ip, alert.get("id"))

    async def _high_alert_playbook(self, ip: str, alert: Dict):
        logger.info(f"PLAYBOOK [High]: Throttling {ip}")
        self.ips.throttle_ip(ip, reason=f"High Priority Alert: {alert.get('name')}")
        self._record_action("Throttling", ip, alert.get("id"))

    def _record_action(self, action: str, ip: str, alert_id: Optional[str]):
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "ip": ip,
            "alert_id": alert_id
        })
        if len(self.execution_history) > 100:
            self.execution_history.pop(0)

    def get_history(self):
        return self.execution_history
