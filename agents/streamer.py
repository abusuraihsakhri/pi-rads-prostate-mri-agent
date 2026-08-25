"""
Live WebSocket Distributed Component Telemetry Streamer for pi-rads-prostate-mri-agent.
"""
import json
import asyncio
from typing import List, Dict, Any

class TelemetryBroadcaster:
    """Broadcasts distributed component reasoning steps in real-time to active WebSocket clients."""

    def __init__(self):
        self.active_connections: List[Any] = []

    async def connect(self, websocket: Any):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: Any):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        msg = json.dumps({"system": "pi-rads-prostate-mri-agent", "event_type": event_type, "payload": data})
        for connection in list(self.active_connections):
            try:
                await connection.send_text(msg)
            except Exception:
                self.disconnect(connection)

GLOBAL_STREAMER = TelemetryBroadcaster()
