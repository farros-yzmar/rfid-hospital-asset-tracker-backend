"""
File: assets.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.2
Date: 2026-04-20

Copyright (c) 2026
"""

from typing import Any

from fastapi import APIRouter

from app.models import RegisterAssetRequest, DeregisterAssetRequest
from app.storage import assets
from app.utils import now_iso
from app.websocket_manager import ws_manager

router = APIRouter(tags=["assets"])


@router.get("/assets")
def get_assets() -> list[dict[str, Any]]:
    """Get all asset records.

    Returns:
        list[dict[str, Any]]: list of assets.
    """
    return list(assets.values())


@router.post("/assets/register")
async def register_Asset(req: RegisterAssetRequest) -> dict[str, Any]:
    """Register a new asset.

    Args:
        req (RegisterAssetRequest): Asset registration payload.

    Returns:
        dict[str, Any]: Registration result.
    """
    asset = {
        "hospital": "",
        "tag_id": req.tag_id,
        "item_name": req.item_name,
        "status": "active",
        "registered_at": now_iso(),
        "last_node_id": "REGISTRATION_DESK",
        "last_seen_at": now_iso(),
    }

    assets[req.tag_id] = asset

    await ws_manager.broadcast_json(
        {
            "type": "asset_registered",
            "asset": asset,
        }
    )

    return {"message": "registered", "asset": asset}


@router.post("/assets/deregister")
async def deregister_asset(req: DeregisterAssetRequest) -> dict[str, Any]:
    """Deregister an existing asset.

    Args:
        req (DeregisterAssetRequest): Asset deregistration payload.

    Returns:
        dict[str, Any]: Deregistration result.
    """
    if req.tag_id not in assets:
        return {"message": "not_found", "tag_id": req.tag_id}

    assets[req.tag_id]["status"] = "deregistered"
    assets[req.tag_id]["last_seen_at"] = now_iso()

    await ws_manager.broadcast_json(
        {
            "type": "asset_deregistered",
            "asset": assets[req.tag_id],
        }
    )

    return {"message": "deregistered", "tag_id": req.tag_id}
