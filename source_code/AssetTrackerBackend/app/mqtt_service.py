"""
File: mqtt_service.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.2
Date: 2026-04-20

Copyright (c) 2026
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import paho.mqtt.client as my_mqtt
from app.storage import assets, nodes
from app.utils import now_iso
from app.websocket_manager import ws_manager


MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

TOPIC_DETECTION = "imh-hospital/checkpoint/detection"
TOPIC_HEARTBEAT = "imh-hospital/checkpoint/heartbeat"


def _schedule_broadcast(message: dict[str, Any]) -> None:
    """Schedule WebSocket broadcast from MQTT thread.

    Args:
        message (dict[str, Any]): Message to send to all WebSocket clients.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast_json(message))
    except RuntimeError:
        # Broadcast can be skipped here unless the loop reference is managed explicitly.
        pass


def on_connect(
    client: my_mqtt.Client,
    user_data: Any,
    flags: dict[str, Any],
    reason_code: Any,
    properties: Any = None,
) -> None:
    """Handle MQTT connect event

    Args:
        client (my_mqtt.Client): MQTT client instance.
        flags (dict[str,Any]): MQTT flags.
        reason_code (Any): Connection result.
        user_data (Any): User data.
        properties (Any, optional): MQTT properties.
    """
    print(f"[MQTT] Connected with reason code: {reason_code}")

    client.subscribe(TOPIC_DETECTION)
    client.subscribe(TOPIC_HEARTBEAT)

    print(f"[MQTT] Connected with reason code: {reason_code}")
    print(f"[MQTT] Connected with reason code: {reason_code}")


def _handle_detection(payload: dict[str, Any]) -> None:
    """Process RFID detection payload.

    Expected payload:
    {
        "tag_id": "...",
        "device_id": "...",
        "room_name": "...",
        "hospital_name": "...",
        "timestamp": "..."
    }

    Args:
        payload (dict[str, Any]): Detection payload.
    """
    device_id = payload.get("device_id")
    room_name = payload.get("room_name", "")
    hospital_name = payload.get("hospital_name", "")
    tag_id = payload.get("tag_id")
    timestamp = payload.get("timestamp", now_iso())

    if not tag_id or not device_id:
        print("[MQTT] Detection payload missing tag_id or node_id")
        return

    if tag_id not in assets:
        print(f"[MQTT] Unknown tag detected: {tag_id}")
        return

    if assets[tag_id].get("status") != "active":
        print(f"[MQTT] Ignoring non-active asset: {tag_id}")
        return

    assets[tag_id]["hospital_name"] = hospital_name
    assets[tag_id]["last_room_name"] = room_name
    assets[tag_id]["last_device_id"] = device_id
    assets[tag_id]["last_seen_at"] = timestamp

    print(f"[MQTT] Detection updated asset: {tag_id}->{room_name} ({device_id})")

    _schedule_broadcast(
        {
            "type": "asset_updated",
            "asset": assets[tag_id],
        }
    )


def _handle_node_status(payload: dict[str, Any]) -> None:
    """Process node heartbeat payload.

    Expected payload examples:

    Heartbeat:
    {
        "hospital": "...",
        "node_id": "...",
        "timestamp": "...",
        "status": "OK"
    }

    Online greeting:
    {
        "hospital": "...",
        "node_id": "...",
        "message": "...",
        "status": "ONLINE",
        "timestamp": "...",
    }

    Offline greeting:
    {
        "hospital": "...",
        "node_id": "...",
        "message": "...",
        "status": "OFFLINE",
        "timestamp": "...",
    }

    Args:
        payload (dict[str, Any]): Heartbeat payload.
    """
    device_id = payload.get("device_id")
    hospital_name = payload.get("hospital_name", "")
    room_name = payload.get("room_name", "")
    message = payload.get("message", "")
    timestamp = payload.get("timestamp", now_iso())
    status = payload.get("status", "")

    if not device_id:
        print(f"[MQTT] Heartbeat payload missing node_id.")
        return

    if device_id not in nodes:
        nodes[device_id] = {
            "device_id": device_id,
            "hospital_name": hospital_name,
            "room_name": room_name,
            "mqtt_host": MQTT_BROKER,
            "mqtt_port": MQTT_PORT,
            "is_provisioned": False,
            "status": "unknown",
            "last_ping_at": "",
            "last_event_at": timestamp,
            "last_message": "",
        }
    nodes[device_id]["hospital_name"] = hospital_name
    nodes[device_id]["room_name"] = room_name
    nodes[device_id]["last_event_at"] = timestamp

    if status == "OK":
        nodes[device_id]["status"] = "online"
        nodes[device_id]["last_ping_at"] = timestamp
        nodes[device_id]["last_message"] = "heartbeat"

        print(f"[MQTT] Heartbeat received from node: {device_id}")

        _schedule_broadcast(
            {
                "type": "node_heartbeat",
                "node": nodes[device_id],
            }
        )
        return

    if status == "ONLINE":
        nodes[device_id]["status"] = "online"
        nodes[device_id]["last_ping_at"] = timestamp
        nodes[device_id]["last_message"] = message or "Hello!"

        print(f"[MQTT] Node online: {device_id}")

        _schedule_broadcast(
            {
                "type": "node_online",
                "node": nodes[device_id],
            }
        )
        return

    if status == "OFFLINE":
        nodes[device_id]["status"] = "offline"
        nodes[device_id]["last_ping_at"] = timestamp
        nodes[device_id]["last_message"] = message or "Goodbye!"

        print(f"[MQTT] Node online: {device_id}")

        _schedule_broadcast(
            {
                "type": "node_offline",
                "node": nodes[device_id],
            }
        )
        return

    print(f"[MQTT] Unknown node status '{status}' from node: {device_id}")


def on_message(
    client: my_mqtt.Client, user_data: Any, msg: my_mqtt.MQTTMessage
) -> None:
    """Handle incoming MQTT message.

    Args:
        client (my_mqtt.Client): MQTT client instance.
        user_data (Any): User data.
        msg (my_mqtt.MQTTMessage): Incoming message.
    """
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception as exc:
        print(f"[MQTT] Invalid JSON payload: {exc}")
        return

    if msg.topic == TOPIC_DETECTION:
        _handle_detection(payload)

    elif msg.topic == TOPIC_HEARTBEAT:
        _handle_node_status(payload)


def mqtt_worker() -> None:
    """Start blocking MQTT loop in a background thread."""
    client = my_mqtt.Client(my_mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print("[MQTT] Connecting to broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


def start_mqtt_background_worker() -> None:
    """Start MQTT worker in a daemon thread."""
    thread = threading.Thread(target=mqtt_worker, daemon=True)
    thread.start()
