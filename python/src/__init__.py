"""
ClaudeBeacon — Memory, Observability, and Audit for Claude Code

Rust core with Python API for integration with Python libraries
"""

from ._core import Beacon as _BeaconCore
from typing import Optional, Dict, Any
import json

__version__ = "0.1.0"


class Beacon:
    """High-level Python API for ClaudeBeacon"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize Beacon with optional database path"""
        if db_path is None:
            db_path = "~/.claude/beacondb/memory.sqlite"
        
        self._core = _BeaconCore(db_path)
        self._core.init(db_path)

    def save_memory(self, context: Dict[str, Any]) -> bool:
        """Save project context to persistent memory"""
        return self._core.save_memory(context)

    def observe(self) -> Dict[str, Any]:
        """Get observability data for current session"""
        result = self._core.observe()
        return json.loads(result) if isinstance(result, str) else result

    def audit(self, filter: Optional[Dict[str, Any]] = None) -> list:
        """Get audit logs with optional filtering"""
        result = self._core.audit(filter)
        logs = json.loads(result) if isinstance(result, str) else result
        return logs if isinstance(logs, list) else []


# Export main API
__all__ = ["Beacon", "__version__"]
