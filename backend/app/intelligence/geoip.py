"""
GeoIP Module — for mapping attack origins.

Uses MaxMind GeoLite2 databases (or similar) to provide 
geographic context to alerts.
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False

from app.utils.config import settings

logger = logging.getLogger(__name__)

class GeoIPLookup:
    """Provides geographic lookup for IP addresses."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.GEOIP_DB_PATH
        self.reader = None
        self._init_reader()

    def _init_reader(self):
        if not GEOIP_AVAILABLE:
            logger.warning("geoip2 library not installed. GeoIP disabled.")
            return

        if self.db_path and os.path.exists(self.db_path):
            try:
                self.reader = geoip2.database.Reader(self.db_path)
                logger.info(f"GeoIP database loaded from {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to load GeoIP database: {e}")
        else:
            logger.warning(f"GeoIP database not found at {self.db_path}")

    def lookup(self, ip: str) -> Dict[str, Any]:
        """Lookup geographic info for an IP."""
        if not self.reader:
            return {}

        try:
            response = self.reader.city(ip)
            return {
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "latitude": response.location.latitude,
                "longitude": response.location.longitude,
                "asn": self._get_asn(ip),
            }
        except Exception:
            return {}

    def _get_asn(self, ip: str) -> Optional[int]:
        return None

    def close(self):
        if self.reader:
            self.reader.close()

# Singleton
geoip_lookup = GeoIPLookup()
