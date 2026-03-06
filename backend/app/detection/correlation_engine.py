"""
Advanced Correlation Engine.

Correlates individual alerts into high-level security Incidents 
using MITRE ATT&CK mapping and temporal relationship analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.models.schemas import Alert, Incident, AttackCategory

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Groups alerts into logical incidents."""
    
    def __init__(self, window_minutes: int = 15):
        self.window = timedelta(minutes=window_minutes)
        self.active_incidents: List[Incident] = []
        self._alert_groups: Dict[str, List[Alert]] = defaultdict(list)

    def correlate(self, alert: Alert) -> Optional[Incident]:
        """Process a new alert and check for correlation with existing alerts."""
        
        # Grouping key: Source IP
        key = alert.source_ip
        self._alert_groups[key].append(alert)
        
        # Cleanup old alerts in this group
        now = datetime.now()
        self._alert_groups[key] = [
            a for a in self._alert_groups[key] 
            if (now - a.timestamp) < self.window
        ]
        
        group = self._alert_groups[key]
        
        # Logic: If 3 or more alerts of different types from same source -> Multi-stage incident
        if len(group) >= 3:
            categories = {a.attack_category for a in group if a.attack_category != AttackCategory.UNKNOWN}
            
            if len(categories) >= 2:
                return self._create_or_update_incident(group, categories)
        
        return None

    def _create_or_update_incident(self, alerts: List[Alert], categories: Set[AttackCategory]) -> Incident:
        source_ip = alerts[0].source_ip
        
        # Check if an incident for this source already exists
        for inc in self.active_incidents:
            if inc.source_ips and source_ip in inc.source_ips:
                inc.alert_ids = list(set(inc.alert_ids + [a.id for a in alerts]))
                inc.attack_categories = list(categories)
                inc.updated_at = datetime.now()
                return inc

        # Create new incident
        new_inc = Incident(
            id=f"INC-{datetime.now().strftime('%Y%m%d')}-{len(self.active_incidents)+1:03d}",
            title=f"Multi-stage attack from {source_ip}",
            description=f"Correlated {len(alerts)} alerts across {len(categories)} ATT&CK categories.",
            severity="high" if len(categories) > 2 else "medium",
            status="open",
            source_ips=[source_ip],
            alert_ids=[a.id for a in alerts],
            attack_categories=list(categories),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.active_incidents.append(new_inc)
        logger.warning(f"NEW INCIDENT CREATED: {new_inc.id} involving {source_ip}")
        return new_inc

# Singleton
correlation_engine = CorrelationEngine()
