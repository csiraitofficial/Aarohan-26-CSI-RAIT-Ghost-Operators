"""
AI Triage & Contextual Analysis — LLM-lite explanations for alerts.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AITriageManager:
    """
    Provides natural language explanations and severity scoring for alerts.
    Uses 'Local AI' logic (heuristics-based templates) for speed, 
    but designed to be swapped with an LLM (Grok/GPT) in Phase 4.
    """

    def __init__(self):
        self.triage_history: List[Dict[str, Any]] = []

    def explain_alert(self, alert_data: Dict[str, Any]) -> str:
        """Generates a human-friendly explanation of why an alert was triggered."""
        alert_name = alert_data.get("name", "Unknown Alert")
        alert_type = alert_data.get("type", "Detection")
        source = alert_data.get("source_ip", "Unknown")
        severity = alert_data.get("severity", "Info")

        explanation = f"The NIDS {alert_type} engine detected a {severity} threat named '{alert_name}' from IP {source}. "
        
        if "ddos" in alert_name.lower() or "flood" in alert_name.lower():
            explanation += "This indicates a potential Denial-of-Service attempt where the source is overwhelming your system with packets. "
        elif "brute" in alert_name.lower():
            explanation += "This suggests an attacker is trying multiple passwords to gain unauthorized access. "
        elif "sqli" in alert_name.lower() or "injection" in alert_name.lower():
            explanation += "The system detected payload patterns typical of SQL Injection, where an attacker tries to steal or corrupt your database data. "
        else:
            explanation += "This behavior is anomalous and warrants immediate investigation by a security analyst."

        return explanation

    def triage(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Performs a full triage, adding explanation and confidence scores."""
        explanation = self.explain_alert(alert_data)
        
        # Automated triage score (0.0 to 1.0)
        score = 0.5
        if alert_data.get("severity") == "critical": score += 0.4
        if alert_data.get("severity") == "high": score += 0.2
        
        triage_info = {
            "alert_id": alert_data.get("id"),
            "ai_explanation": explanation,
            "triage_score": min(score, 1.0),
            "timestamp": datetime.now().isoformat()
        }
        
        self.triage_history.append(triage_info)
        if len(self.triage_history) > 1000:
            self.triage_history.pop(0)

        return triage_info

    def get_stats(self):
        return {
            "triaged_alerts": len(self.triage_history),
            "avg_triage_score": sum(t["triage_score"] for t in self.triage_history) / max(1, len(self.triage_history))
        }
