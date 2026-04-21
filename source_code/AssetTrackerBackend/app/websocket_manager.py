"""
File: websocket_manager.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.1
Date: 2026-04-16

Copyright (c) 2026
"""

from typing import Any
from fastapi import WebSocket


class ConnectionManager:
    """Manage active WS clients."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        dead_connections: list[WebSocket] = []

        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        for ws in dead_connections:
            self.disconnect(ws)


ws_manager = ConnectionManager()
