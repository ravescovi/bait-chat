"""
bAIt-Chat: AI-powered assistant for Bluesky beamline control

A comprehensive AI assistant that integrates with Bluesky QueueServer
to provide natural language interaction with synchrotron beamlines.
"""

__version__ = "0.2.0"
__author__ = "bAIt-Chat Development Team"
__email__ = "support@bait-chat.dev"

# Core imports
from .backend.config import Settings
from .backend.models import DeviceResponse, ExplainRequest, ExplainResponse, PlanResponse

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Settings",
    "DeviceResponse",
    "PlanResponse",
    "ExplainRequest",
    "ExplainResponse",
]
