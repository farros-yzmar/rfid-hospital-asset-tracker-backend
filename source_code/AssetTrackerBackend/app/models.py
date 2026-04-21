"""
File: models.py
Author: Farros Ramzy (you@domain.com)
Description: Description
Version: 0.2
Date: 2026-04-20

Copyright (c) 2026
"""

from pydantic import BaseModel, Field


class RegisterAssetRequest(BaseModel):
    tag_id: str = Field(min_length=1)
    item_name: str = Field(min_length=1)
    # reg_date: str = Field(min_length=1)


class DeregisterAssetRequest(BaseModel):
    tag_id: str = Field(min_length=1)


class RegisterNodeRequest(BaseModel):
    device_id: str = Field(min_length=1)
    hospital_name: str = Field(min_length=1)
    room_name: str = Field(min_length=1)
    mqtt_host: str = Field(min_length=1)
    mqtt_port: int = 1883
    # room_name: str = node_id


class ProvisionNodeRequest(BaseModel):
    """docstring for ProvisionNodeRequest."""

    device_id: str = Field(min_length=1)


class ProvisionNodeRespose(BaseModel):
    """docstring for ProvisionNodeRespose."""

    is_provisioned: bool
    hospital_name: str = ""
    room_name: str = ""
    mqtt_host: str = "broker.hivemq.com"
    mqtt_port: int = 1883
