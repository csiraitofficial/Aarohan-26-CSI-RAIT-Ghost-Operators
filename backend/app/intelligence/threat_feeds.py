"""
Threat Intelligence Module — STIX/TAXII and IOC management.

Integrates with external threat feeds to identify known malicious 
IPs, domains, and file hashes.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ThreatIntelManager:
    """Manages Indicators of Compromise (IOCs) from various feeds."""
    
    def __init__(self):
        self.malicious_ips: Set[str] = set()
        self.malicious_domains: Set[str] = set()
        self.last_update: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def update_feeds(self):
        """Fetch updates from external feeds."""
        async with self._lock:
            logger.info("Updating threat intelligence feeds...")
            # Example: Fetching from a community feed (mock)
            # In a real scenario, use TAXII client or API calls to AbuseIPDB, VirusTotal, etc.
            await self._fetch_abuse_ipdb()
            self.last_update = datetime.now()
            logger.info(f"Threat intel updated: {len(self.malicious_ips)} IPs tracked.")

    async def _fetch_abuse_ipdb(self):
        """Mock implementation for AbuseIPDB integration."""
        # Realistic implementation would use API keys from settings
        # For now, we seed with common malicious IPs for testing
        mock_iocs = ["185.220.101.1", "45.146.164.110", "193.142.146.35"]
        for ip in mock_iocs:
            self.malicious_ips.add(ip)

    def is_malicious(self, ip: str) -> bool:
        """Check if an IP is in the known malicious list."""
        return ip in self.malicious_ips

    def get_ioc_details(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get context for a malicious IP."""
        if self.is_malicious(ip):
            return {
                "source": "AbuseIPDB",
                "confidence": 95,
                "first_seen": (datetime.now() - timedelta(days=2)).isoformat(),
                "tags": ["tor-exit-node", "brute-force"]
            }
        return None

# Singleton
threat_intel = ThreatIntelManager()
