"""
WebSocket Manager — real-time event broadcasting.

Entirely NEW module (not in original NIDS).
Replaces HTTP polling with persistent WebSocket connections.
"""

import json
import asyncio
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class WSManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.add(ws)
        logger.info(f"WS connected ({len(self._connections)} total)")

    async def disconnect(self, ws: WebSocket):
        self._connections.discard(ws)
        logger.info(f"WS disconnected ({len(self._connections)} total)")

    async def broadcast(self, event: str, data: Dict[str, Any]):
        """Broadcast a JSON message to all connected clients."""
        message = json.dumps({"event": event, "data": data}, default=str)
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self._connections -= dead

    def broadcast_sync(self, data: Dict[str, Any]):
        """
        Thread-safe synchronous broadcast wrapper.
        Called from the orchestrator's processing threads.
        """
        if not self._connections or not self._loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast("alert", data), self._loop
            )
        except Exception:
            pass

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton
ws_manager = WSManager()
