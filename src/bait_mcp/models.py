"""
Pydantic models for bAIt-Chat API
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class DeviceResponse(BaseModel):
    devices: Dict[str, Any]


class PlanResponse(BaseModel):
    plans: Dict[str, Any]


class ExplainRequest(BaseModel):
    plan_name: str
    parameters: Optional[Dict[str, Any]] = None


class ExplainResponse(BaseModel):
    plan_name: str
    explanation: str
    parameters: Optional[Dict[str, Any]] = None


class QServerStatus(BaseModel):
    status: str
    manager_state: str
    devices_in_queue: int
    plans_in_queue: int
