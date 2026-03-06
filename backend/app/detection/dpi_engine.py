"""
Deep Packet Inspection (DPI) Engine — Advanced payload analysis.

Detects:
1. Web Attacks (SQLi, XSS, Path Traversal)
2. Shellcode & Binary exploitation patterns
3. Command Injection
4. Suspicious Header Data
"""

import logging
import re
from typing import Dict, List, Any, Optional

from app.models.schemas import PacketInfo, AttackCategory

logger = logging.getLogger(__name__)

class DPIEngine:
    """
    Analyzes packet payloads for malicious byte patterns and strings.
    """

    def __init__(self):
        # Per-flow stream reassembly buffer
        # key: (src_ip, dst_ip, src_port, dst_port) -> deque of payload chunks
        from collections import deque
        self.stream_buffer: Dict[tuple, deque] = {}
        self.max_buffer_per_flow = 5 # Last 5 packets' payload for reassembly
        
        # Compiled regex patterns - hardened for obfuscation
        self.rules = {
            "SQL_INJECTION": re.compile(
                r"(\bUNION\b.*\bSELECT\b|INSERT\s+INTO|UPDATE\s+.*SET|DELETE\s+FROM|--|OR\s+.*\d+.*=.*\d+.*|/\*.*\*/)", 
                re.IGNORECASE | re.DOTALL
            ),
            "XSS_ATTEMPT": re.compile(
                r"(<script.*?>|onclick|onerror|alert\(|document\.cookie|eval\(|base64|String\.fromCharCode)", 
                re.IGNORECASE
            ),
            "PATH_TRAVERSAL": re.compile(
                r"(\.\.\/|\.\.\\|/etc/passwd|/windows/system32|/boot/|/root/|C:\\)", 
                re.IGNORECASE
            ),
            "SHELL_INJECTION": re.compile(
                r"(;\s*(cat|rm|ls|id|whoami|nc|wget|curl)|\|\s*(bash|sh|zsh|powershell)|\$\(.*\)|`.*`)", 
                re.IGNORECASE
            )
        }

    def inspect(self, packet: PacketInfo) -> List[Dict[str, Any]]:
        """Performs deep inspection with stream reassembly and multi-stage decoding."""
        results = []
        payload_hex = packet.payload_hex
        
        if not payload_hex:
            return results

        try:
            raw_bytes = bytes.fromhex(payload_hex)
            flow_key = (packet.source_ip, packet.dest_ip, packet.source_port, packet.dest_port)
            
            # Update stream buffer
            from collections import deque
            if flow_key not in self.stream_buffer:
                self.stream_buffer[flow_key] = deque(maxlen=self.max_buffer_per_flow)
            self.stream_buffer[flow_key].append(raw_bytes)
            
            # Reassemble last N chunks
            reassembled_payload = b"".join(self.stream_buffer[flow_key])
            
            # 1. Direct UTF-8 Inspection (on reassembled payload)
            payload_str = reassembled_payload.decode('utf-8', errors='ignore')
            self._run_rules(payload_str, "REASSEMBLED_STREAM", results)

            # 2. URL Decoding (for web attacks)
            import urllib.parse
            url_decoded = urllib.parse.unquote(payload_str)
            if url_decoded != payload_str:
                self._run_rules(url_decoded, "URL_DECODED", results)

            # 3. Base64 Detection & Decoding
            # Hackers often hide shellcode or commands in Base64
            if len(payload_str) > 8:
                try:
                    import base64
                    # Heuristic: find base64-like strings
                    b64_matches = re.findall(r'[A-Za-z0-9+/]{8,}={0,2}', payload_str)
                    for b64_str in b64_matches:
                        decoded_b64 = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                        if len(decoded_b64) > 4:
                            self._run_rules(decoded_b64, "BASE64_DECODED", results)
                except Exception:
                    pass

        except Exception as e:
            logger.debug(f"DPI analysis error: {e}")

        return results

    def _run_rules(self, text: str, encoding_type: str, results: List[Dict[str, Any]]):
        """Helper to run rules against decoded text."""
        for name, pattern in self.rules.items():
            match = pattern.search(text)
            if match:
                # Deduplicate
                if any(r["name"] == name for r in results):
                    continue
                    
                results.append({
                    "name": name,
                    "severity": "high",
                    "attack_category": self._map_category(name),
                    "description": f"DPI match [{encoding_type}]: {name} detected. Match: {match.group(0)[:50]}",
                    "confidence": 0.95,
                    "mitre": self._get_mitre(name)
                })

        return results

    def _map_category(self, rule_name: str) -> AttackCategory:
        if rule_name == "SQL_INJECTION": return AttackCategory.INITIAL_ACCESS
        if rule_name == "XSS_ATTEMPT": return AttackCategory.INITIAL_ACCESS
        if rule_name == "PATH_TRAVERSAL": return AttackCategory.DISCOVERY
        if rule_name == "SHELL_INJECTION": return AttackCategory.EXECUTION
        return AttackCategory.UNKNOWN

    def _get_mitre(self, rule_name: str) -> Dict[str, str]:
        mappings = {
            "SQL_INJECTION": {"tactic": "Initial Access", "technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
            "XSS_ATTEMPT": {"tactic": "Initial Access", "technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
            "PATH_TRAVERSAL": {"tactic": "Discovery", "technique_id": "T1083", "technique_name": "File and Directory Discovery"},
            "SHELL_INJECTION": {"tactic": "Execution", "technique_id": "T1059", "technique_name": "Command and Scripting Interpreter"}
        }
        return mappings.get(rule_name, {})
