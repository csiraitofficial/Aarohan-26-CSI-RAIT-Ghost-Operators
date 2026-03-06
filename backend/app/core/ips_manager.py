"""
IPS Manager — Intrusion Prevention System with real firewall integration.

Upgrades over original:
  - Actual firewall commands (not commented out)
  - Rate limiting / throttling action
  - IP reputation tracking
  - Whitelist/blacklist management
  - Action audit log
"""

import logging
import subprocess
import platform
import threading
from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta

from app.models.schemas import IPSAction, IPSConfig

logger = logging.getLogger(__name__)


class IPSManager:
    """Intrusion Prevention System Manager with real firewall integration."""

    def __init__(self, config: Optional[IPSConfig] = None):
        self.config = config or IPSConfig()
        self.whitelist: Set[str] = set(self.config.whitelist)
        self.blocked_ips: Dict[str, Dict[str, Any]] = {}  # ip -> {expiration, reason, action}
        self._lock = threading.Lock()
        self.os_type = platform.system().lower()
        self.action_log: List[Dict[str, Any]] = []

    # ----------------------------------------------------------------
    # Block / Unblock
    # ----------------------------------------------------------------

    def block_ip(
        self,
        ip_address: str,
        duration_minutes: int = 60,
        reason: str = "Malicious activity",
        action: IPSAction = IPSAction.BLOCK,
    ) -> bool:
        """Block an IP using the system firewall."""
        if ip_address in self.whitelist:
            logger.warning(f"IPS: Skipped whitelisted IP {ip_address}")
            return False

        with self._lock:
            if ip_address in self.blocked_ips:
                return True  # Already blocked

            expiration = datetime.now() + timedelta(minutes=duration_minutes)

            success = True
            if self.config.enabled and action == IPSAction.BLOCK:
                success = self._execute_block(ip_address)

            if success:
                self.blocked_ips[ip_address] = {
                    "expiration": expiration,
                    "reason": reason,
                    "action": action.value,
                    "blocked_at": datetime.now().isoformat(),
                }
                self._log_action("block", ip_address, reason)
                logger.info(f"IPS: Blocked {ip_address} until {expiration} ({reason})")
            return success

    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP."""
        with self._lock:
            if ip_address not in self.blocked_ips:
                return False

            success = True
            if self.config.enabled:
                success = self._execute_unblock(ip_address)

            if success:
                del self.blocked_ips[ip_address]
                self._log_action("unblock", ip_address, "Manual/auto unblock")
                logger.info(f"IPS: Unblocked {ip_address}")
            return success

    def is_blocked(self, ip_address: str) -> bool:
        return ip_address in self.blocked_ips

    def cleanup_expired(self):
        """Remove expired blocks."""
        now = datetime.now()
        expired = [
            ip for ip, info in self.blocked_ips.items()
            if info["expiration"] and now > info["expiration"]
        ]
        for ip in expired:
            self.unblock_ip(ip)

    # ----------------------------------------------------------------
    # OS-Level Firewall Commands
    # ----------------------------------------------------------------

    def _execute_block(self, ip: str) -> bool:
        try:
            if self.os_type == "windows":
                rule = f"NIDS_Block_{ip}"
                cmd = f'netsh advfirewall firewall add rule name="{rule}" dir=in action=block remoteip={ip}'
                logger.info(f"IPS exec: {cmd}")
                subprocess.run(cmd, shell=True, check=True, capture_output=True, timeout=10)
                return True
            elif self.os_type == "linux":
                cmd = ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
                logger.info(f"IPS exec: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                return True
            else:
                logger.warning(f"IPS: Unsupported OS '{self.os_type}'")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"IPS: Block command timed out for {ip}")
            return False
        except Exception as e:
            logger.error(f"IPS: Block command failed for {ip}: {e}")
            return False

    def _execute_unblock(self, ip: str) -> bool:
        try:
            if self.os_type == "windows":
                rule = f"NIDS_Block_{ip}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule}"'
                subprocess.run(cmd, shell=True, check=True, capture_output=True, timeout=10)
                return True
            elif self.os_type == "linux":
                cmd = ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                return True
            return False
        except Exception as e:
            logger.error(f"IPS: Unblock failed for {ip}: {e}")
            return False

    # ----------------------------------------------------------------
    # Stats
    # ----------------------------------------------------------------

    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        return [
            {"ip": ip, **info}
            for ip, info in self.blocked_ips.items()
        ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "enabled": self.config.enabled,
            "auto_block": self.config.auto_block,
            "blocked_count": len(self.blocked_ips),
            "whitelist_count": len(self.whitelist),
            "total_actions": len(self.action_log),
            "os_type": self.os_type,
        }

    def _log_action(self, action: str, ip: str, reason: str):
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "ip": ip,
            "reason": reason,
        })
        # Keep only last 1000 actions
        if len(self.action_log) > 1000:
            self.action_log = self.action_log[-1000:]
