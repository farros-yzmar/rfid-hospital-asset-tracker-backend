"""
File: ws.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.1
Date: 2026-04-16

Copyright (c) 2026
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.storage import assets, nodes
from app.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for live monitor updates.

    Args:
        websocket (WebSocket): Active websocket connection.
    """
    await ws_manager.connect(websocket)

    try:
        await websocket.send_json(
            {
                "type": "snapshot",
                "assets": list(assets.values()),
                "nodes": list(nodes.values()),
            }
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
