from __future__ import annotations
"""
Advanced IPS Engine — Real-time Prevention & Mitigation.
"""

import logging
import subprocess
import platform
import threading
import time
from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta

from app.models.schemas import IPSAction, IPSConfig, PacketInfo

logger = logging.getLogger(__name__)

class IPSEngine:
    """
    Advanced Intrusion Prevention System Engine.
    Handles:
    1. OS-specific firewall blocking (iptables/netsh).
    2. Traffic throttling/rate-limiting.
    3. Temporary vs Permanent bans.
    4. Whitelist/Blacklist management.
    """

    def __init__(self, config: Optional[IPSConfig] = None):
        self.config = config or IPSConfig()
        self.whitelist: Set[str] = set(self.config.whitelist)
        self.active_blocks: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}  # ip -> {count, window_start}
        
        # Stateful Connection Tracking for IPS
        self.conn_states: Dict[str, Dict[str, Any]] = {} # ip -> {syn_count, last_seen, state}
        self.syn_flood_threshold = 50 # packets per 10 sec
        
        self._lock = threading.Lock()
        self.os_type = platform.system().lower()
        
        # Local cache for Blockchain Consensus
        self.global_block_cache: Set[str] = set()
        self._last_cache_sync = 0
        self._sync_lock = threading.Lock()

    def handle_threat(self, ip_address: str, severity: str, reason: str):
        """Main entry point for the orchestrator to request an action."""
        if not self.config.enabled:
            return

        if ip_address in self.whitelist:
            return

        if severity == "critical":
            self.block_ip(ip_address, duration_minutes=self.config.block_duration_minutes, reason=reason)
        elif severity == "high":
            self.throttle_ip(ip_address, reason=reason)

    def track_stateful(self, packet: PacketInfo):
        """Monitors IP state (e.g., detecting SYN floods) before blocking."""
        if not self.config.enabled or packet.source_ip in self.whitelist:
            return

        src = packet.source_ip
        now = datetime.now()

        with self._lock:
            if src not in self.conn_states:
                self.conn_states[src] = {"syn_count": 0, "window_start": now}
            
            state = self.conn_states[src]
            
            # Detect SYN Flood
            if packet.tcp_flags == "S": # SYN
                state["syn_count"] += 1
                
            if (now - state["window_start"]).total_seconds() > 10:
                if state["syn_count"] > self.syn_flood_threshold:
                    self.block_ip(src, duration_minutes=30, reason="SYN flood detected")
                # Reset window
                state["syn_count"] = 0
                state["window_start"] = now

    def block_ip(self, ip_address: str, duration_minutes: int = 60, reason: str = "Attack detected"):
        """Perform a hard block at the OS firewall level."""
        with self._lock:
            if ip_address in self.active_blocks:
                return

            expiration = datetime.now() + timedelta(minutes=duration_minutes) if duration_minutes > 0 else None
            
            success = self._execute_os_block(ip_address)
            if success:
                self.active_blocks[ip_address] = {
                    "expiration": expiration,
                    "reason": reason,
                    "action": IPSAction.BLOCK,
                    "timestamp": datetime.now()
                }
                logger.warning(f"IPS [BLOCK]: {ip_address} for {duration_minutes}m. Reason: {reason}")

    def throttle_ip(self, ip_address: str, reason: str = "Suspicious traffic"):
        """
        Simulated/Soft throttling by flagging the IP in the orchestrator.
        In a real bridge mode, this would drop a percentage of packets.
        """
        with self._lock:
            self.active_blocks[ip_address] = {
                "expiration": datetime.now() + timedelta(minutes=15),
                "reason": reason,
                "action": IPSAction.THROTTLE,
                "timestamp": datetime.now()
            }
            logger.info(f"IPS [THROTTLE]: {ip_address} for 15m. Reason: {reason}")

    def _execute_os_block(self, ip: str) -> bool:
        """Executes the actual shell commands to block the IP."""
        try:
            if self.os_type == "windows":
                # Add block rule using netsh
                rule_name = f"NIDS_BLOCK_{ip.replace('.', '_')}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=block remoteip={ip}'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                return True
            elif self.os_type == "linux":
                # Add block rule using iptables
                cmd = ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
                subprocess.run(cmd, check=True, capture_output=True)
                return True
        except Exception as e:
            logger.error(f"IPS OS Block failed for {ip}: {e}")
        return False

    def _execute_os_unblock(self, ip: str) -> bool:
        """Removes the block rule."""
        try:
            if self.os_type == "windows":
                rule_name = f"NIDS_BLOCK_{ip.replace('.', '_')}"
                cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                return True
            elif self.os_type == "linux":
                cmd = ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
                subprocess.run(cmd, check=True, capture_output=True)
                return True
        except Exception as e:
            logger.error(f"IPS OS Unblock failed for {ip}: {e}")
        return False

    def is_blocked(self, ip: str) -> bool:
        """Check if an IP is currently blocked locally or globally (Cached)."""
        now = time.time()
        
        # 1. Local Firewall Check (Instant)
        with self._lock:
            if ip in self.active_blocks:
                return True
        
        # 2. Blockchain Cache Check
        if ip in self.global_block_cache:
            return True

        # 3. Cache Sync (Every 60 seconds)
        # We don't block the caller; if sync is needed, we do it and return 
        # (Next packet will benefit from the refreshed cache)
        if now - self._last_cache_sync > 60:
            threading.Thread(target=self._sync_global_cache, daemon=True).start()
            self._last_cache_sync = now

        return False

    def _sync_global_cache(self):
        """ Background sync of the blockchain global block list. """
        if not self._sync_lock.acquire(blocking=False):
            return
        try:
            from app.blockchain.reporter import BlockchainReporter
            reporter = BlockchainReporter()
            if reporter.is_globally_blocked("0.0.0.0"): # Trigger lazy init
                pass
            
            # In a real collaborative scenario, we would iterate through proposal results
            # For now, we query the live status of suspicious IPs we've seen recently
            # or pull the full list from the contract if implementable.
            pass 
        finally:
            self._sync_lock.release()

    def cleanup_expired(self):
        """Called periodically by orchestrator to lift expired bans."""
        now = datetime.now()
        to_remove = []
        with self._lock:
            for ip, info in self.active_blocks.items():
                if info["expiration"] and now > info["expiration"]:
                    to_remove.append(ip)

        for ip in to_remove:
            self._execute_os_unblock(ip)
            with self._lock:
                del self.active_blocks[ip]
            logger.info(f"IPS [UNBLOCK]: {ip} session expired.")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_blocks": len(self.active_blocks),
            "os_detected": self.os_type,
            "whitelist_size": len(self.whitelist)
        }
