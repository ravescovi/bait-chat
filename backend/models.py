"""
Pydantic models for request/response schemas
Defines data structures for API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# Enums for common types

class PlanStatus(str, Enum):
    """Status of a plan execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    PAUSED = "paused"


class DeviceType(str, Enum):
    """Types of beamline devices"""
    MOTOR = "motor"
    DETECTOR = "detector"
    SIGNAL = "signal"
    FLYER = "flyer"
    AREA_DETECTOR = "area_detector"
    TEMPERATURE_CONTROLLER = "temperature_controller"
    OTHER = "other"


# Device-related models

class DeviceComponent(BaseModel):
    """Component of a device"""
    name: str
    type: str
    readable: bool = True
    writable: bool = False
    value: Optional[Any] = None


class DeviceResponse(BaseModel):
    """Response model for device information"""
    name: str = Field(..., description="Device name as used in plans")
    type: DeviceType = Field(..., description="Type of device")
    description: str = Field("", description="Human-readable description")
    components: List[DeviceComponent] = Field(default_factory=list, description="Device components")
    is_readable: bool = Field(True, description="Can be read from")
    is_movable: bool = Field(False, description="Can be moved/set")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "motor_x",
                "type": "motor",
                "description": "Sample X position motor",
                "components": [
                    {"name": "position", "type": "float", "readable": True, "writable": True},
                    {"name": "velocity", "type": "float", "readable": True, "writable": True}
                ],
                "is_readable": True,
                "is_movable": True,
                "metadata": {"units": "mm", "limits": [-10, 10]}
            }
        }


# Plan-related models

class PlanParameter(BaseModel):
    """Parameter definition for a plan"""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Optional[Any] = None


class PlanResponse(BaseModel):
    """Response model for plan information"""
    name: str = Field(..., description="Plan name")
    description: str = Field("", description="Plan description")
    parameters: List[PlanParameter] = Field(default_factory=list, description="Plan parameters")
    module: str = Field("", description="Module containing the plan")
    is_generator: bool = Field(True, description="Is this a generator function")
    enhanced_description: Optional[str] = Field(None, description="Enhanced description from RAG")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "scan",
                "description": "Perform a scan over a motor range",
                "parameters": [
                    {"name": "detectors", "type": "list", "required": True},
                    {"name": "motor", "type": "str", "required": True},
                    {"name": "start", "type": "float", "required": True},
                    {"name": "stop", "type": "float", "required": True},
                    {"name": "num", "type": "int", "required": True}
                ],
                "module": "bluesky.plans",
                "is_generator": True
            }
        }


# Scan metadata models

class ScanStatistics(BaseModel):
    """Statistics from a scan"""
    max_counts: Optional[float] = None
    min_counts: Optional[float] = None
    mean_counts: Optional[float] = None
    total_counts: Optional[float] = None
    num_points: Optional[int] = None


class ScanMetadata(BaseModel):
    """Metadata for a completed scan"""
    scan_id: str = Field(..., description="Unique scan identifier")
    uid: str = Field(..., description="Short UID")
    timestamp: datetime = Field(..., description="Scan timestamp")
    plan_name: str = Field(..., description="Name of the plan executed")
    plan_args: Dict[str, Any] = Field(default_factory=dict, description="Plan arguments")
    exit_status: PlanStatus = Field(..., description="Exit status")
    duration: float = Field(..., description="Scan duration in seconds")
    motors: List[str] = Field(default_factory=list, description="Motors used")
    detectors: List[str] = Field(default_factory=list, description="Detectors used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    statistics: Optional[ScanStatistics] = Field(None, description="Scan statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
                "uid": "a1b2c3d4",
                "timestamp": "2024-01-15T10:30:00",
                "plan_name": "scan",
                "plan_args": {
                    "motor": "motor_x",
                    "start": 0.0,
                    "stop": 5.0,
                    "num": 51
                },
                "exit_status": "completed",
                "duration": 125.4,
                "motors": ["motor_x"],
                "detectors": ["pilatus"],
                "metadata": {
                    "sample": "test_sample_001",
                    "energy": 12.4
                }
            }
        }


# Explanation models

class ExplainRequest(BaseModel):
    """Request to explain a plan"""
    plan_name: Optional[str] = Field(None, description="Name of predefined plan")
    plan_source: Optional[str] = Field(None, description="Python source code of plan")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    @validator('plan_source')
    def validate_source_or_name(cls, v, values):
        if not v and not values.get('plan_name'):
            raise ValueError('Either plan_name or plan_source must be provided')
        return v


class ExplainResponse(BaseModel):
    """Response with plan explanation"""
    plan_name: Optional[str] = None
    explanation: str = Field(..., description="Plain English explanation")
    timestamp: datetime = Field(default_factory=datetime.now)


# Queue management models (Phase 1.5)

class QueueItem(BaseModel):
    """Item in the queue"""
    uid: str = Field(..., description="Unique item ID")
    name: str = Field(..., description="Plan name")
    args: List[Any] = Field(default_factory=list, description="Plan arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Plan keyword arguments")
    user: str = Field("", description="User who submitted")
    user_group: str = Field("", description="User group")
    item_type: str = Field("plan", description="Type of queue item")


class QueueStatus(BaseModel):
    """Queue status information"""
    running_item: Optional[QueueItem] = None
    plan_queue: List[QueueItem] = Field(default_factory=list)
    queue_size: int = Field(0)
    running: bool = Field(False)
    manager_state: str = Field("idle")
    re_state: str = Field("idle")


class PlanSubmission(BaseModel):
    """Plan submission request"""
    name: str = Field(..., description="Plan name")
    args: List[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Plan metadata")
    
    @validator('name')
    def validate_plan_name(cls, v):
        # In production, check against whitelist
        forbidden_plans = ["dangerous_plan", "admin_only"]
        if v in forbidden_plans:
            raise ValueError(f"Plan '{v}' is not allowed")
        return v


# NLP/Agent models

class NLPQuery(BaseModel):
    """Natural language query for agent"""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Query context")


class AgentResponse(BaseModel):
    """Response from LangChain agent"""
    response: str = Field(..., description="Agent response")
    action_taken: Optional[str] = Field(None, description="Action performed")
    plan_generated: Optional[PlanSubmission] = Field(None, description="Generated plan")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


# Error models

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


# Search models

class SearchResult(BaseModel):
    """Result from knowledge base search"""
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Document source")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response from search endpoint"""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(0)


# Voice input models (optional)

class VoiceInput(BaseModel):
    """Voice input data"""
    audio_data: str = Field(..., description="Base64 encoded audio")
    format: str = Field("wav", description="Audio format")
    sample_rate: int = Field(16000, description="Sample rate in Hz")


class TranscriptionResponse(BaseModel):
    """Response from voice transcription"""
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    language: str = Field("en", description="Detected language")


# WebSocket models for real-time updates

class WSMessage(BaseModel):
    """WebSocket message structure"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class QueueUpdate(WSMessage):
    """Queue status update via WebSocket"""
    type: str = Field("queue_update")
    queue_status: QueueStatus


class ScanProgress(WSMessage):
    """Scan progress update via WebSocket"""
    type: str = Field("scan_progress")
    scan_id: str
    progress: float = Field(ge=0.0, le=1.0)
    current_point: int
    total_points: int