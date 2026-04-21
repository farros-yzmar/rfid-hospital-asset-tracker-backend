"""
File: main.py
Author: Farros Ramzy (you@domain.com)
Description: Asset Tracker Backend entrypoint
Version: 0.1
Date: 2026-04-15

Copyright (c) 2026
"""

from fastapi import FastAPI

from app.mqtt_service import start_mqtt_background_worker
from app.routes.assets import router as assets_router
from app.routes.nodes import router as nodes_router
from app.routes.ws import router as ws_router

app = FastAPI(title="Hospital Asset Tracker Backend")

app.include_router(assets_router)
app.include_router(nodes_router)
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event() -> None:
    start_mqtt_background_worker()

@app.get("/")
def root() -> dict[str, str]:
    """AI is creating summary for root

    Returns:
        dict[str, str]: [description]
    """
    return {"message": "Asset Tracker Backend is Running"}


@app.get("/health")
def health() -> dict[str, str]:
    """AI is creating summary for health

    Returns:
        dict[str, str]: [description]
    """
    return {"status": "ok"}
