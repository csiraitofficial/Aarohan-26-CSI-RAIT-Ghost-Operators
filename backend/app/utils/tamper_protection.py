"""
Log Tamper Protection — Local Merkle-tree based integrity monitoring.
"""

import hashlib
import os
import json
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LogIntegrityManager:
    """
    Maintains a rolling hash chain for logs to detect tampering.
    """
    def __init__(self, state_file: str = "data/log_integrity.json"):
        self.state_file = state_file
        self.last_hash: str = ""
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.last_hash = data.get("last_hash", "")
            except Exception:
                self.last_hash = ""

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump({
                "last_hash": self.last_hash,
                "last_updated": datetime.now().isoformat()
            }, f)

    def secure_log(self, log_entry: str):
        """Adds a log entry to the hash chain."""
        combined = f"{self.last_hash}{log_entry}".encode()
        self.last_hash = hashlib.sha256(combined).hexdigest()
        self._save_state()

    def verify_integrity(self, log_lines: List[str]) -> bool:
        """Verifies the integrity of a set of logs against the stored chain."""
        current_hash = ""
        for line in log_lines:
            combined = f"{current_hash}{line}".encode()
            current_hash = hashlib.sha256(combined).hexdigest()
        
        return current_hash == self.last_hash

    def get_last_hash(self):
        return self.last_hash
