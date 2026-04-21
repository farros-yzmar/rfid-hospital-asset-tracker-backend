"""
File: nodes.py
Author: Farros ramzy (you@domain.com)
Description: Description
Version: 0.2
Date: 2026-04-20

Copyright (c) 2026
"""

from typing import Any

from fastapi import APIRouter

from app.models import RegisterNodeRequest, ProvisionNodeRequest
from app.storage import nodes
from app.utils import now_iso
from app.websocket_manager import ws_manager

router = APIRouter(tags=["nodes"])


@router.get("/nodes")
def get_nodes() -> list[dict[str, Any]]:
    """Get all registered nodes.

    Returns:
        list[dict[str, Any]]: List of nodes.
    """
    return list(nodes.values())


@router.post("/nodes/register")
async def register_node(req: RegisterNodeRequest) -> dict[str, Any]:
    """Register a new node.

    Args:
        req (RegisterNodeRequest): Node registration payload.

    Returns:
        dict[str,Any]: Registration result.
    """
    device_id = req.device_id

    node = nodes.get(device_id, {})

    node.update(
        {
            "device_id": req.device_id,
            "hospital_name": req.hospital_name,
            "room_name": req.room_name,
            "mqtt_host": req.mqtt_host,
            "mqtt_port": req.mqtt_port,
            "is_provisioned": True,
            "status": node.get("status", "online"),
            "last_ping_at": node.get("last_ping_at", now_iso()),
            "last_event_at": now_iso(),
            "last_message": "registered",
        }
    )

    nodes[device_id] = node

    await ws_manager.broadcast_json(
        {
            "type": "node_registered",
            "node": node,
        }
    )

    return {"message": "node_registered", "node": node}


@router.post("/nodes/provision")
def provision_node(req: ProvisionNodeRequest) -> dict[str, Any]:
    node = nodes.get(req.device_id)

    if node is None:
        nodes[req.device_id] = {
            "device_id": req.device_id,
            "hospital_name": "",
            "room_name": "",
            "mqtt_host": "broker.hivemq.com",
            "mqtt_port": 1883,
            "is_provisioned": False,
            "status": "unassigned",
            "last_ping_at": "",
            "last_event_at": now_iso(),
            "last_message": "awaiting provisioning",
        }
        return {
            "is_provisioned": False,
            "hospital_name": "",
            "room_name": "",
            "mqtt_host": "",
            "mqtt_port": 1883,
        }
    return {
        "is_provisioned": node.get("is_provisioned", False),
        "hospital_name": node.get("hospital_name", ""),
        "room_name": node.get("room_name", ""),
        "mqtt_host": node.get("mqtt_host", ""),
        "mqtt_port": node.get("mqtt_port", 1883),
    }
