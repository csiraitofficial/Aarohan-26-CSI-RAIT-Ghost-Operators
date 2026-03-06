"""
Suricata Rule Parser — for industry-standard signature detection.

This module parses Suricata-style '.rules' files and integrates them 
into the signature detection engine.

Format example:
alert tcp $EXTERNAL_NET any -> $HTTP_SERVERS 80 (msg:"ET EXPLOIT SQLi"; content:"SELECT";)
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.models.schemas import AlertSeverity, AttackCategory, MITREMapping

logger = logging.getLogger(__name__)

class Action(Enum):
    ALERT = "alert"
    DROP = "drop"
    PASS = "pass"
    REJECT = "reject"

@dataclass
class SuricataRule:
    action: str
    protocol: str
    src_ip: str
    src_port: str
    direction: str
    dst_ip: str
    dst_port: str
    msg: str
    sid: int
    rev: int
    content: List[str]
    severity: AlertSeverity
    attack_category: AttackCategory
    raw: str

class SuricataParser:
    """Parses Suricata rule files into structured objects."""
    
    # Simple regex for Suricata rule structure
    # action proto src_ip src_port direction dst_ip dst_port (options)
    RULE_REGEX = r"^(?P<action>\w+)\s+(?P<proto>\w+)\s+(?P<src_ip>\S+)\s+(?P<src_port>\S+)\s+(?P<direction>->|<>)\s+(?P<dst_ip>\S+)\s+(?P<dst_port>\S+)\s+\((?P<options>.*)\)$"
    
    OPTION_REGEX = r"(?P<key>\w+):\"?(?P<value>[^\";]+)\"?;"

    def parse_file(self, filepath: str) -> List[SuricataRule]:
        rules = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    rule = self.parse_line(line)
                    if rule:
                        rules.append(rule)
        except Exception as e:
            logger.error(f"Failed to parse Suricata file {filepath}: {e}")
        
        return rules

    def parse_line(self, line: str) -> Optional[SuricataRule]:
        match = re.match(self.RULE_REGEX, line)
        if not match:
            return None
        
        data = match.groupdict()
        options_raw = data['options']
        
        options = {}
        content_list = []
        
        for opt_match in re.finditer(self.OPTION_REGEX, options_raw):
            key = opt_match.group('key')
            val = opt_match.group('value')
            if key == 'content':
                content_list.append(val)
            else:
                options[key] = val
        
        # Map metadata to our schema
        severity = self._map_severity(options.get('classtype', ''))
        category = self._map_category(options.get('classtype', ''))
        
        return SuricataRule(
            action=data['action'],
            protocol=data['proto'].upper(),
            src_ip=data['src_ip'],
            src_port=data['src_port'],
            direction=data['direction'],
            dst_ip=data['dst_ip'],
            dst_port=data['dst_port'],
            msg=options.get('msg', 'Unnamed Suricata Rule'),
            sid=int(options.get('sid', 0)),
            rev=int(options.get('rev', 1)),
            content=content_list,
            severity=severity,
            attack_category=category,
            raw=line
        )

    def _map_severity(self, classtype: str) -> AlertSeverity:
        low = ["successful-admin", "unsuccessful-user"]
        med = ["web-application-attack", "denial-of-service", "trojan-activity"]
        high = ["exploit-kit", "system-call-detect", "shellcode-detect"]
        
        if any(c in classtype for c in high): return AlertSeverity.HIGH
        if any(c in classtype for c in med): return AlertSeverity.MEDIUM
        if any(c in classtype for c in low): return AlertSeverity.LOW
        return AlertSeverity.INFO

    def _map_category(self, classtype: str) -> AttackCategory:
        mapping = {
            "web-application-attack": AttackCategory.INITIAL_ACCESS,
            "denial-of-service": AttackCategory.IMPACT,
            "trojan-activity": AttackCategory.COMMAND_AND_CONTROL,
            "credential-theft": AttackCategory.CREDENTIAL_ACCESS,
            "network-scan": AttackCategory.RECONNAISSANCE,
        }
        for k, v in mapping.items():
            if k in classtype:
                return v
        return AttackCategory.UNKNOWN
