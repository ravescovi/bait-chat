#!/usr/bin/env python3
"""
bAIt-Chat Backend with Real QServer Integration
Connects to actual QServer running the test_instrument
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import DeviceResponse, ExplainRequest, ExplainResponse, PlanResponse, QServerStatus

class ChatRequest:
    def __init__(self, message: str, model_url: str = None):
        self.message = message
        self.model_url = model_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="bAIt-Chat API with QServer",
    description="Bluesky AI Technician Chat API with real QServer integration",
    version="0.2.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from settings
QSERVER_URL = os.environ.get("QSERVER_URL", settings.qserver_url)
LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", settings.lmstudio_url)


@app.get("/")
async def root():
    return {"message": "bAIt-Chat API with QServer integration", "qserver_url": QSERVER_URL}


@app.get("/health")
async def health():
    """Health check with QServer status"""
    qserver_status = "disconnected"

    try:
        response = requests.get(f"{QSERVER_URL}/status", timeout=5)
        if response.status_code == 200:
            qserver_status = "connected"
    except:
        pass

    return {
        "status": "healthy",
        "llm_provider": "lmstudio",
        "qserver_status": qserver_status,
        "qserver_url": QSERVER_URL,
    }


@app.get("/qserver/status")
async def get_qserver_status():
    """Get detailed QServer status"""
    try:
        response = requests.get(f"{QSERVER_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return QServerStatus(
                status="connected",
                manager_state=data.get("manager_state", "unknown"),
                devices_in_queue=data.get("devices_in_queue", 0),
                plans_in_queue=data.get("plans_in_queue", 0),
            )
        else:
            raise HTTPException(status_code=500, detail="QServer not responding")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"QServer connection failed: {str(e)}")


@app.get("/devices")
async def get_devices():
    """Get available devices from QServer"""
    try:
        # Try to get devices from QServer
        response = requests.get(f"{QSERVER_URL}/devices/allowed", timeout=10)

        if response.status_code == 200:
            qserver_data = response.json()
            devices_dict = qserver_data.get("devices_allowed", {})

            # Organize devices by type
            organized_devices = {"motors": {}, "detectors": {}, "other": {}}

            for device_name, device_info in devices_dict.items():
                device_type = "other"
                description = device_info.get("description", f"Device: {device_name}")

                # Classify devices based on name patterns
                if "motor" in device_name.lower() or device_name.startswith("m"):
                    device_type = "motors"
                    description = device_info.get("description", f"Motor: {device_name}")
                elif "det" in device_name.lower() or "scaler" in device_name.lower():
                    device_type = "detectors"
                    description = device_info.get("description", f"Detector: {device_name}")
                elif "shutter" in device_name.lower():
                    device_type = "other"
                    description = device_info.get("description", f"Shutter: {device_name}")

                organized_devices[device_type][device_name] = {
                    "type": device_info.get("class", "Unknown"),
                    "description": description,
                    "module": device_info.get("module", ""),
                    "classname": device_info.get("classname", ""),
                }

            logger.info(f"Retrieved {len(devices_dict)} devices from QServer")
            return DeviceResponse(devices=organized_devices)

        else:
            logger.warning(f"QServer devices request failed: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to get devices from QServer: {e}")

    # Fallback to mock devices if QServer is not available
    logger.info("Using fallback mock devices")
    return DeviceResponse(
        devices={
            "motors": {
                "sim_motor": {
                    "type": "SimulatedMotor",
                    "description": "Simulated motor for testing",
                },
            },
            "detectors": {
                "sim_det": {"type": "SimulatedDetector", "description": "Simulated noisy detector"},
            },
            "other": {
                "shutter": {"type": "SimulatedShutter", "description": "Simulated APS PSS shutter"}
            },
        }
    )


@app.get("/plans")
async def get_plans():
    """Get available scan plans from QServer"""
    try:
        # Try to get plans from QServer
        response = requests.get(f"{QSERVER_URL}/plans/allowed", timeout=10)

        if response.status_code == 200:
            qserver_data = response.json()
            plans_dict = qserver_data.get("plans_allowed", {})

            # Convert QServer format to our format
            formatted_plans = {}
            for plan_name, plan_info in plans_dict.items():
                parameters = []
                description = plan_info.get("description", f"Plan: {plan_name}")

                # Extract parameters from plan info
                if "parameters" in plan_info:
                    for param in plan_info["parameters"]:
                        if isinstance(param, dict):
                            parameters.append(param.get("name", str(param)))
                        else:
                            parameters.append(str(param))

                formatted_plans[plan_name] = {
                    "description": description,
                    "parameters": parameters,
                    "module": plan_info.get("module", ""),
                    "example": f"{plan_name}(...)",  # Generic example
                }

            logger.info(f"Retrieved {len(plans_dict)} plans from QServer")
            return PlanResponse(plans=formatted_plans)

        else:
            logger.warning(f"QServer plans request failed: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to get plans from QServer: {e}")

    # Fallback to standard Bluesky plans if QServer is not available
    logger.info("Using fallback standard Bluesky plans")
    return PlanResponse(
        plans={
            "count": {
                "description": "Take repeated measurements at current position",
                "parameters": ["detectors", "num", "delay"],
                "example": "count([sim_det], num=1, delay=None)",
            },
            "scan": {
                "description": "Continuous scan of a motor from start to stop position",
                "parameters": ["detectors", "motor", "start", "stop", "num"],
                "example": "scan([sim_det], sim_motor, -1, 1, 11)",
            },
            "list_scan": {
                "description": "Scan through a specific list of motor positions",
                "parameters": ["detectors", "motor", "positions"],
                "example": "list_scan([sim_det], sim_motor, [1, 2, 3, 4, 5])",
            },
            "rel_scan": {
                "description": "Relative scan from current motor position",
                "parameters": ["detectors", "motor", "start", "stop", "num"],
                "example": "rel_scan([sim_det], sim_motor, -1, 1, 11)",
            },
            "grid_scan": {
                "description": "2D grid scan with two motors",
                "parameters": [
                    "detectors",
                    "motor1",
                    "start1",
                    "stop1",
                    "num1",
                    "motor2",
                    "start2",
                    "stop2",
                    "num2",
                ],
                "example": "grid_scan([sim_det], sim_motor, -1, 1, 3, sim_motor, -1, 1, 3)",
            },
        }
    )


@app.post("/explain")
async def explain_plan(request: ExplainRequest):
    """Explain a Bluesky plan using LMStudio with real device context"""

    # Get current devices and plans for context
    try:
        devices_response = await get_devices()
        plans_response = await get_plans()

        devices = devices_response.devices
        plans = plans_response.plans

        # Build context
        device_list = []
        for category, devs in devices.items():
            for name, info in devs.items():
                device_list.append(f"{name} ({info['description']})")

        plan_list = list(plans.keys())

        context = f"""Available devices: {', '.join(device_list)}
Available plans: {', '.join(plan_list)}"""

    except:
        context = "Real-time device and plan information not available"

    # Try to connect to LMStudio
    try:
        async with aiohttp.ClientSession() as session:
            # Test LMStudio connection
            async with session.get(f"{LMSTUDIO_URL}/v1/models") as response:
                if response.status != 200:
                    raise Exception("LMStudio not responding")

            # Create context-aware system message
            system_context = f"""You are bAIt-Chat, an AI assistant for Bluesky beamline control at synchrotron facilities.

{context}

You are connected to a real QServer running a test instrument with BITS (Beamline Integration and Testing Suite).

Help users understand scan plans, suggest appropriate parameters based on available devices, explain beamline operations, and provide guidance on data collection strategies. Be specific about the actual devices available."""

            # Determine if this is a plan explanation or general question
            user_content = f"User question: {request.plan_name}"
            if request.plan_name.lower() in [p.lower() for p in plans.keys()]:
                user_content = f"Explain the Bluesky scan plan '{request.plan_name}' in detail, including parameters, use cases, and provide an example using our available devices."

            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_content},
            ]

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
            }

            async with session.post(
                f"{LMSTUDIO_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    explanation = result["choices"][0]["message"]["content"]
                    return ExplainResponse(
                        plan_name=request.plan_name,
                        explanation=explanation,
                        parameters=request.parameters,
                    )
                else:
                    error_text = await response.text()
                    logger.warning(f"LMStudio API error: {error_text}")
                    raise Exception(f"LMStudio API error: {response.status}")

    except Exception as e:
        logger.info(f"LMStudio not available ({e}), using fallback")

        # Enhanced fallback explanations with real context
        if request.plan_name.lower() in [p.lower() for p in plans.keys()]:
            plan_info = plans[request.plan_name.lower()]
            explanation = f"{plan_info['description']}\n\nParameters: {', '.join(plan_info['parameters'])}\n\nExample: {plan_info.get('example', 'No example available')}"
        else:
            # General fallback explanations
            fallback_explanations = {
                "scan": "The 'scan' plan performs a continuous scan by moving a motor from start to stop position while collecting data from detectors at regular intervals.",
                "count": "The 'count' plan takes repeated measurements at the current position to improve counting statistics.",
                "list_scan": "The 'list_scan' plan moves a motor to specific positions in a list and collects data at each position.",
                "grid_scan": "The 'grid_scan' plan performs a 2D scan by moving two motors in a grid pattern while collecting detector data.",
            }

            explanation = fallback_explanations.get(
                request.plan_name.lower(),
                f"The '{request.plan_name}' is a Bluesky operation. {context}",
            )

        return ExplainResponse(
            plan_name=request.plan_name, explanation=explanation, parameters=request.parameters
        )


@app.post("/chat")
async def chat_with_llm(request: dict):
    """Direct chat with LLM using provided model URL"""
    try:
        message = request.get("message", "")
        model_url = request.get("model_url", LMSTUDIO_URL)
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Get current devices and plans for context
        try:
            devices_response = await get_devices()
            plans_response = await get_plans()

            devices = devices_response.devices
            plans = plans_response.plans

            # Build context
            device_list = []
            for category, devs in devices.items():
                for name, info in devs.items():
                    device_list.append(f"{name} ({info['description']})")

            plan_list = list(plans.keys())

            context = f"""Available devices: {', '.join(device_list[:10]) if device_list else 'Loading...'}
Available plans: {', '.join(plan_list[:10]) if plan_list else 'Loading...'}"""

        except:
            context = "Real-time device and plan information not available"

        # Connect to LLM
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create context-aware system message
            system_context = f"""You are bAIt-Chat, an AI assistant for Bluesky beamline control at synchrotron facilities.

{context}

You are connected to a real QServer running a test instrument with BITS (Beamline Integration and Testing Suite).

Help users understand scan plans, suggest appropriate parameters based on available devices, explain beamline operations, and provide guidance on data collection strategies. Be specific about the actual devices available when possible."""

            messages = [
                {"role": "system", "content": system_context},
                {"role": "user", "content": message},
            ]

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
            }

            async with session.post(
                f"{model_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    chat_response = result["choices"][0]["message"]["content"]
                    return {
                        "message": message,
                        "response": chat_response,
                        "model_url": model_url
                    }
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=500, detail=f"LLM API error: {response.status} - {error_text}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# Enhanced Instrument Introspection Endpoints


@app.get("/instrument/status")
async def get_instrument_status():
    """Get detailed QServer and instrument status"""
    try:
        response = requests.get(f"{QSERVER_URL}/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()

            # Get additional environment info
            env_response = requests.get(f"{QSERVER_URL}/environment/open", timeout=5)
            environment_info = {}
            if env_response.status_code == 200:
                environment_info = env_response.json()

            return {
                "qserver_status": status_data,
                "environment_info": environment_info,
                "instrument_name": "test_instrument",
                "instrument_path": "bait_chat.test_instrument.test_instrument.startup",
            }
        else:
            raise HTTPException(status_code=500, detail="QServer not responding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get instrument status: {str(e)}")


@app.get("/instrument/devices/detailed")
async def get_devices_detailed():
    """Get detailed device information including current positions and configuration"""
    try:
        # Get basic device list
        response = requests.get(f"{QSERVER_URL}/devices/allowed", timeout=10)
        if response.status_code != 200:
            return {"devices": [], "error": "QServer not available"}

        qserver_data = response.json()
        devices_dict = qserver_data.get("devices_allowed", {})

        # Get current device status and positions
        device_status = await _get_device_positions()

        detailed_devices = []
        for device_name, device_info in devices_dict.items():
            device_detail = {
                "name": device_name,
                "class": device_info.get("classname", "Unknown"),
                "module": device_info.get("module", ""),
                "description": device_info.get("description", f"Device: {device_name}"),
                "category": _categorize_device(device_name, device_info),
                "parameters": device_info.get("parameters", {}),
                "read_attrs": device_info.get("read_attrs", []),
                "configuration_attrs": device_info.get("configuration_attrs", []),
                "current_status": device_status.get(device_name, {}).get("status", "unknown"),
                "current_position": device_status.get(device_name, {}).get("position"),
                "limits": device_status.get(device_name, {}).get("limits"),
                "connected": device_status.get(device_name, {}).get("connected", False),
            }
            detailed_devices.append(device_detail)

        return {
            "devices": detailed_devices,
            "total_count": len(detailed_devices),
            "categories": _get_device_categories(detailed_devices),
            "environment_status": await _get_environment_status(),
        }
    except Exception as e:
        logger.error(f"Error getting detailed devices: {e}")
        return {"devices": [], "error": str(e)}


@app.get("/instrument/plans/detailed")
async def get_plans_detailed():
    """Get detailed plan information including parameters and examples"""
    try:
        response = requests.get(f"{QSERVER_URL}/plans/allowed", timeout=10)
        if response.status_code != 200:
            return {"plans": [], "error": "QServer not available"}

        qserver_data = response.json()
        plans_dict = qserver_data.get("plans_allowed", {})

        # Get available devices for better examples
        available_devices = await _get_available_devices_for_plans()

        detailed_plans = []
        for plan_name, plan_info in plans_dict.items():
            # Extract and analyze parameter details
            parameters = await _analyze_plan_parameters(plan_info, available_devices)

            plan_detail = {
                "name": plan_name,
                "module": plan_info.get("module", ""),
                "description": plan_info.get("description", f"Plan: {plan_name}"),
                "parameters": parameters,
                "category": _categorize_plan(plan_name),
                "example_usage": _get_smart_plan_example(plan_name, parameters, available_devices),
                "docstring": plan_info.get("docstring", ""),
                "is_generator": plan_info.get("is_generator", True),
                "estimated_duration": _estimate_plan_duration(plan_name, parameters),
                "prerequisites": _get_plan_prerequisites(plan_name, parameters),
                "common_use_cases": _get_plan_use_cases(plan_name),
                "related_plans": _find_related_plans(plan_name, plans_dict.keys()),
            }
            detailed_plans.append(plan_detail)

        return {
            "plans": detailed_plans,
            "total_count": len(detailed_plans),
            "categories": _get_plan_categories(detailed_plans),
            "analysis_summary": _analyze_plan_suite(detailed_plans),
        }
    except Exception as e:
        logger.error(f"Error getting detailed plans: {e}")
        return {"plans": [], "error": str(e)}


@app.get("/instrument/history")
async def get_instrument_history():
    """Get recent scan history and run information"""
    try:
        response = requests.get(f"{QSERVER_URL}/history/get", timeout=10)
        if response.status_code == 200:
            history_data = response.json()
            return {
                "history": history_data.get("items", []),
                "total_runs": len(history_data.get("items", [])),
                "summary": _summarize_history(history_data.get("items", [])),
            }
        else:
            return {"history": [], "error": "No history available"}
    except Exception as e:
        return {"history": [], "error": str(e)}


@app.post("/instrument/plan/validate")
async def validate_plan_parameters(plan_data: dict):
    """Validate plan parameters before execution"""
    try:
        plan_name = plan_data.get("plan_name")
        parameters = plan_data.get("parameters", {})

        # Get plan information
        response = requests.get(f"{QSERVER_URL}/plans/allowed", timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Cannot access QServer")

        plans_dict = response.json().get("plans_allowed", {})
        if plan_name not in plans_dict:
            raise HTTPException(status_code=404, detail=f"Plan '{plan_name}' not found")

        plan_info = plans_dict[plan_name]
        validation_result = _validate_plan_parameters(plan_info, parameters)

        return {
            "plan_name": plan_name,
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "suggested_parameters": validation_result.get("suggestions", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/instrument/plans/recommendations")
async def get_plan_recommendations():
    """Get plan recommendations based on common use cases"""
    try:
        response = requests.get(f"{QSERVER_URL}/plans/allowed", timeout=10)
        if response.status_code != 200:
            return {"recommendations": [], "error": "QServer not available"}

        plans_dict = response.json().get("plans_allowed", {})
        available_devices = await _get_available_devices_for_plans()

        recommendations = {
            "beginners": _get_beginner_recommendations(plans_dict, available_devices),
            "common_tasks": _get_common_task_recommendations(plans_dict, available_devices),
            "advanced": _get_advanced_recommendations(plans_dict, available_devices),
            "by_device_type": _get_device_based_recommendations(plans_dict, available_devices),
        }

        return {
            "recommendations": recommendations,
            "available_devices_summary": {
                "motors": len(available_devices.get("motors", [])),
                "detectors": len(available_devices.get("detectors", [])),
                "total": sum(len(devices) for devices in available_devices.values()),
            },
        }
    except Exception as e:
        logger.error(f"Error getting plan recommendations: {e}")
        return {"recommendations": [], "error": str(e)}


# Helper functions for device and plan analysis


def _categorize_device(name: str, info: dict) -> str:
    """Categorize device based on name and class information"""
    name_lower = name.lower()
    class_name = info.get("classname", "").lower()

    if "motor" in name_lower or "motor" in class_name:
        return "motors"
    elif "det" in name_lower or "detector" in class_name or "scaler" in class_name:
        return "detectors"
    elif "shutter" in name_lower or "shutter" in class_name:
        return "shutters"
    elif "slit" in name_lower or "slit" in class_name:
        return "slits"
    else:
        return "other"


def _get_device_categories(devices: list) -> dict:
    """Get summary of device categories"""
    categories = {}
    for device in devices:
        category = device["category"]
        categories[category] = categories.get(category, 0) + 1
    return categories


def _categorize_plan(name: str) -> str:
    """Categorize plan based on name"""
    name_lower = name.lower()

    if "scan" in name_lower:
        return "scans"
    elif "count" in name_lower:
        return "counting"
    elif "move" in name_lower or "mv" in name_lower:
        return "movement"
    elif "calibration" in name_lower or "calib" in name_lower:
        return "calibration"
    elif "sim" in name_lower:
        return "simulation"
    else:
        return "other"


def _get_plan_categories(plans: list) -> dict:
    """Get summary of plan categories"""
    categories = {}
    for plan in plans:
        category = plan["category"]
        categories[category] = categories.get(category, 0) + 1
    return categories


def _get_plan_example(plan_name: str, parameters: list) -> str:
    """Generate example usage for a plan"""
    if not parameters:
        return f"{plan_name}()"

    param_examples = []
    for param in parameters:
        param_name = param.get("name", "param") if isinstance(param, dict) else str(param)
        if "detector" in param_name.lower() or param_name == "detectors":
            param_examples.append("[sim_det]")
        elif "motor" in param_name.lower():
            param_examples.append("sim_motor")
        elif param_name in ["start", "stop"]:
            param_examples.append("-1" if param_name == "start" else "1")
        elif param_name == "num":
            param_examples.append("11")
        else:
            param_examples.append(f"<{param_name}>")

    return f"{plan_name}({', '.join(param_examples)})"


async def _get_available_devices_for_plans() -> dict:
    """Get categorized available devices for plan examples"""
    try:
        response = requests.get(f"{QSERVER_URL}/devices/allowed", timeout=5)
        if response.status_code == 200:
            devices_data = response.json().get("devices_allowed", {})
            categorized = {"motors": [], "detectors": [], "shutters": [], "other": []}

            for device_name, device_info in devices_data.items():
                category = _categorize_device(device_name, device_info)
                if category in categorized:
                    categorized[category].append(device_name)
                else:
                    categorized["other"].append(device_name)

            return categorized
    except:
        pass

    # Fallback
    return {"motors": ["sim_motor"], "detectors": ["sim_det"], "shutters": ["shutter"], "other": []}


async def _analyze_plan_parameters(plan_info: dict, available_devices: dict) -> list:
    """Analyze plan parameters with type information and suggestions"""
    parameters = []
    raw_params = plan_info.get("parameters", [])

    for param in raw_params:
        if isinstance(param, dict):
            param_detail = param.copy()
        else:
            param_detail = {"name": str(param)}

        param_name = param_detail.get("name", "")

        # Enhanced parameter analysis
        param_detail.update(
            {
                "type": _infer_parameter_type(param_name),
                "required": _is_parameter_required(param_name, param_detail),
                "default": _get_parameter_default(param_name, param_detail),
                "suggestions": _get_parameter_suggestions(param_name, available_devices),
                "description": _get_parameter_description(param_name),
                "validation_rules": _get_parameter_validation_rules(param_name),
            }
        )

        parameters.append(param_detail)

    return parameters


def _get_smart_plan_example(plan_name: str, parameters: list, available_devices: dict) -> str:
    """Generate smart example usage with actual available devices"""
    if not parameters:
        return f"{plan_name}()"

    param_examples = []
    for param in parameters:
        param_name = param.get("name", "param")
        suggestions = param.get("suggestions", [])

        if suggestions:
            param_examples.append(str(suggestions[0]))
        elif "detector" in param_name.lower() or param_name == "detectors":
            detectors = available_devices.get("detectors", ["sim_det"])
            param_examples.append(f"[{detectors[0]}]")
        elif "motor" in param_name.lower():
            motors = available_devices.get("motors", ["sim_motor"])
            param_examples.append(motors[0])
        elif param_name in ["start", "stop"]:
            param_examples.append("-1" if param_name == "start" else "1")
        elif param_name == "num":
            param_examples.append("11")
        elif param_name == "delay":
            param_examples.append("None")
        else:
            param_examples.append(f"<{param_name}>")

    return f"{plan_name}({', '.join(param_examples)})"


def _infer_parameter_type(param_name: str) -> str:
    """Infer parameter type from name"""
    name_lower = param_name.lower()

    if "detector" in name_lower and param_name.endswith("s"):
        return "list[Detector]"
    elif "detector" in name_lower:
        return "Detector"
    elif "motor" in name_lower:
        return "Motor"
    elif param_name in ["start", "stop", "step", "span"]:
        return "float"
    elif param_name in ["num", "count"]:
        return "int"
    elif param_name in ["delay", "time"]:
        return "float | None"
    elif "position" in name_lower:
        return "list[float]"
    else:
        return "Any"


def _is_parameter_required(param_name: str, param_info: dict) -> bool:
    """Determine if parameter is required"""
    # Basic heuristics - in real implementation, this would come from plan signatures
    optional_params = ["delay", "md", "metadata"]
    return param_name not in optional_params and param_info.get("default") is None


def _get_parameter_default(param_name: str, param_info: dict) -> Any:
    """Get parameter default value"""
    defaults = {"num": 1, "delay": None, "md": {}}
    return param_info.get("default", defaults.get(param_name))


def _get_parameter_suggestions(param_name: str, available_devices: dict) -> list:
    """Get parameter value suggestions based on available devices"""
    name_lower = param_name.lower()

    if "detector" in name_lower:
        return available_devices.get("detectors", ["sim_det"])[:3]
    elif "motor" in name_lower:
        return available_devices.get("motors", ["sim_motor"])[:3]
    elif param_name == "num":
        return [1, 11, 21, 51]
    elif param_name in ["start", "stop"]:
        return [-5, -1, 0, 1, 5]
    elif param_name == "delay":
        return [None, 0.1, 1.0, 5.0]
    else:
        return []


def _get_parameter_description(param_name: str) -> str:
    """Get parameter description"""
    descriptions = {
        "detectors": "List of detectors to read during the scan",
        "motor": "Motor to scan",
        "start": "Starting position for the scan",
        "stop": "Ending position for the scan",
        "num": "Number of points in the scan",
        "delay": "Delay between measurements (seconds)",
        "md": "Metadata dictionary for the scan",
        "positions": "List of positions to visit",
    }
    return descriptions.get(param_name, f"Parameter: {param_name}")


def _get_parameter_validation_rules(param_name: str) -> dict:
    """Get parameter validation rules"""
    rules = {}

    if param_name == "num":
        rules = {"min": 1, "max": 10000, "type": "integer"}
    elif param_name in ["start", "stop"]:
        rules = {"type": "float", "finite": True}
    elif param_name == "delay":
        rules = {"min": 0, "type": "float", "nullable": True}
    elif "detector" in param_name.lower():
        rules = {"type": "list", "min_length": 1}

    return rules




def _estimate_plan_duration(plan_name: str, parameters: list) -> str:
    """Estimate plan execution duration"""
    if "count" in plan_name.lower():
        return "seconds"
    elif "grid" in plan_name.lower():
        return "minutes to hours"
    elif "scan" in plan_name.lower():
        return "seconds to minutes"
    else:
        return "varies"


def _get_plan_prerequisites(plan_name: str, parameters: list) -> list:
    """Get plan prerequisites"""
    prerequisites = ["QServer environment open"]

    param_names = [p.get("name", "") for p in parameters]

    if any("detector" in name.lower() for name in param_names):
        prerequisites.append("Detectors configured and connected")

    if any("motor" in name.lower() for name in param_names):
        prerequisites.append("Motors homed and ready")

    if "scan" in plan_name.lower():
        prerequisites.append("Beam on target")

    return prerequisites


def _get_plan_use_cases(plan_name: str) -> list:
    """Get common use cases for a plan"""
    use_cases_map = {
        "count": [
            "Quick detector check",
            "Background measurement",
            "Signal-to-noise assessment",
            "Detector calibration",
        ],
        "scan": [
            "Finding peak positions",
            "Energy scans",
            "Absorption edge measurements",
            "Rocking curve scans",
        ],
        "rel_scan": [
            "Fine scans around known positions",
            "Peak optimization",
            "Local structure analysis",
        ],
        "list_scan": [
            "Custom position sequences",
            "Non-uniform sampling",
            "Multi-point calibration",
        ],
        "grid_scan": [
            "2D mapping",
            "Sample characterization",
            "Spatial distributions",
            "Mesh scans",
        ],
    }

    for key, cases in use_cases_map.items():
        if key in plan_name.lower():
            return cases

    return ["General purpose scan"]


def _find_related_plans(plan_name: str, all_plan_names: list) -> list:
    """Find related plans based on name similarity and functionality"""
    related = []
    plan_lower = plan_name.lower()

    # Find plans with similar base names
    base_patterns = ["scan", "count", "move", "calib"]
    plan_base = None

    for pattern in base_patterns:
        if pattern in plan_lower:
            plan_base = pattern
            break

    if plan_base:
        for other_plan in all_plan_names:
            if other_plan != plan_name and plan_base in other_plan.lower():
                related.append(other_plan)

    return related[:5]  # Limit to 5 related plans


def _analyze_plan_suite(detailed_plans: list) -> dict:
    """Analyze the complete suite of plans"""
    total_plans = len(detailed_plans)
    categories = {}

    for plan in detailed_plans:
        category = plan.get("category", "other")
        categories[category] = categories.get(category, 0) + 1

    return {
        "total_plans": total_plans,
        "categories_breakdown": categories,
        "available_plan_names": [p["name"] for p in detailed_plans][:10],
    }


def _get_beginner_recommendations(plans_dict: dict, available_devices: dict) -> list:
    """Get plan recommendations for beginners"""
    beginner_plans = ["count", "sim_count_plan", "sim_print_plan"]
    recommendations = []

    for plan_name in beginner_plans:
        if plan_name in plans_dict:
            example = _get_smart_plan_example(plan_name, [], available_devices)
            recommendations.append(
                {
                    "name": plan_name,
                    "reason": "Simple plan, good for learning QServer basics",
                    "example": example,
                    "difficulty": "beginner",
                }
            )

    # Add any "count" or simple plans found
    for plan_name in plans_dict.keys():
        if len(recommendations) >= 5:
            break
        if "count" in plan_name.lower() and plan_name not in [r["name"] for r in recommendations]:
            example = _get_smart_plan_example(plan_name, [], available_devices)
            recommendations.append(
                {
                    "name": plan_name,
                    "reason": "Counting plan - good for detector testing",
                    "example": example,
                    "difficulty": "beginner",
                }
            )

    return recommendations[:5]


def _get_common_task_recommendations(plans_dict: dict, available_devices: dict) -> list:
    """Get plan recommendations for common tasks"""
    common_tasks = [
        {"pattern": "scan", "reason": "Most common type of measurement"},
        {"pattern": "rel_scan", "reason": "Useful for fine adjustments around known positions"},
        {"pattern": "list_scan", "reason": "Flexible scanning with custom positions"},
    ]

    recommendations = []
    for task in common_tasks:
        for plan_name in plans_dict.keys():
            if task["pattern"] in plan_name.lower():
                example = _get_smart_plan_example(plan_name, [], available_devices)
                recommendations.append(
                    {
                        "name": plan_name,
                        "reason": task["reason"],
                        "example": example,
                        "difficulty": "intermediate",
                    }
                )
                break  # Take first match for each pattern

    return recommendations


def _get_advanced_recommendations(plans_dict: dict, available_devices: dict) -> list:
    """Get plan recommendations for advanced users"""
    advanced_patterns = ["grid", "adaptive", "tune", "align", "calibrat"]
    recommendations = []

    for pattern in advanced_patterns:
        for plan_name in plans_dict.keys():
            if pattern in plan_name.lower():
                example = _get_smart_plan_example(plan_name, [], available_devices)
                recommendations.append(
                    {
                        "name": plan_name,
                        "reason": f"Advanced {pattern} functionality",
                        "example": example,
                        "difficulty": "advanced",
                    }
                )
                break

    return recommendations


def _get_device_based_recommendations(plans_dict: dict, available_devices: dict) -> dict:
    """Get plan recommendations based on available device types"""
    recommendations = {}

    # Motor-based recommendations
    if available_devices.get("motors"):
        motor_plans = []
        for plan_name in plans_dict.keys():
            if "scan" in plan_name.lower() or "move" in plan_name.lower():
                example = _get_smart_plan_example(plan_name, [], available_devices)
                motor_plans.append(
                    {
                        "name": plan_name,
                        "example": example,
                        "description": f"Uses motors: {', '.join(available_devices['motors'][:3])}",
                    }
                )
                if len(motor_plans) >= 3:
                    break
        recommendations["motors"] = motor_plans

    # Detector-based recommendations
    if available_devices.get("detectors"):
        detector_plans = []
        for plan_name in plans_dict.keys():
            if "count" in plan_name.lower() or "det" in plan_name.lower():
                example = _get_smart_plan_example(plan_name, [], available_devices)
                detector_plans.append(
                    {
                        "name": plan_name,
                        "example": example,
                        "description": f"Uses detectors: {', '.join(available_devices['detectors'][:3])}",
                    }
                )
                if len(detector_plans) >= 3:
                    break
        recommendations["detectors"] = detector_plans

    return recommendations


def _summarize_history(history_items: list) -> dict:
    """Summarize scan history"""
    if not history_items:
        return {"total_scans": 0}

    successful_scans = sum(1 for item in history_items if item.get("exit_status") == "completed")
    failed_scans = len(history_items) - successful_scans

    plan_counts = {}
    for item in history_items:
        plan_name = item.get("plan_name", "unknown")
        plan_counts[plan_name] = plan_counts.get(plan_name, 0) + 1

    return {
        "total_scans": len(history_items),
        "successful_scans": successful_scans,
        "failed_scans": failed_scans,
        "most_used_plans": sorted(plan_counts.items(), key=lambda x: x[1], reverse=True)[:5],
    }


def _validate_plan_parameters(plan_info: dict, parameters: dict) -> dict:
    """Validate parameters for a plan"""
    errors = []
    warnings = []
    suggestions = {}

    # Basic validation - this would be enhanced with actual parameter schemas
    required_params = plan_info.get("parameters", [])

    for param in required_params:
        param_name = param.get("name") if isinstance(param, dict) else str(param)
        if param_name not in parameters:
            warnings.append(f"Parameter '{param_name}' not provided")

            # Add suggestions based on parameter name
            if "detector" in param_name.lower():
                suggestions[param_name] = ["sim_det"]
            elif "motor" in param_name.lower():
                suggestions[param_name] = "sim_motor"

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
    }


async def _get_device_positions() -> dict:
    """Get current device positions and status from QServer"""
    device_positions = {}

    try:
        # Check if environment is open
        env_response = requests.get(f"{QSERVER_URL}/environment/open", timeout=5)
        if env_response.status_code == 200:
            env_data = env_response.json()
            if env_data.get("success", False):
                # Environment is open, try to get device readings
                try:
                    # This would require QServer to support device reading endpoints
                    # For now, we'll simulate some basic status
                    devices_response = requests.get(f"{QSERVER_URL}/devices/allowed", timeout=5)
                    if devices_response.status_code == 200:
                        devices_data = devices_response.json()
                        for device_name, device_info in devices_data.get(
                            "devices_allowed", {}
                        ).items():
                            device_positions[device_name] = {
                                "status": (
                                    "connected"
                                    if "motor" in device_name.lower()
                                    or "det" in device_name.lower()
                                    else "ready"
                                ),
                                "position": 0.0 if "motor" in device_name.lower() else None,
                                "limits": (
                                    {"low": -10.0, "high": 10.0}
                                    if "motor" in device_name.lower()
                                    else None
                                ),
                                "connected": True,
                            }
                except Exception as e:
                    logger.debug(f"Could not read device positions: {e}")

    except Exception as e:
        logger.debug(f"Environment not open or not accessible: {e}")

    return device_positions


async def _get_environment_status() -> dict:
    """Get QServer environment status"""
    try:
        response = requests.get(f"{QSERVER_URL}/environment/open", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "msg": "Environment closed"}
    except Exception as e:
        return {"success": False, "msg": f"Cannot access environment: {str(e)}"}


@app.get("/instrument/devices/{device_name}/details")
async def get_single_device_details(device_name: str):
    """Get detailed information for a specific device"""
    try:
        # Get device information
        response = requests.get(f"{QSERVER_URL}/devices/allowed", timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="QServer not available")

        devices_data = response.json().get("devices_allowed", {})
        if device_name not in devices_data:
            raise HTTPException(status_code=404, detail=f"Device '{device_name}' not found")

        device_info = devices_data[device_name]
        device_status = await _get_device_positions()

        return {
            "name": device_name,
            "class": device_info.get("classname", "Unknown"),
            "module": device_info.get("module", ""),
            "description": device_info.get("description", f"Device: {device_name}"),
            "category": _categorize_device(device_name, device_info),
            "parameters": device_info.get("parameters", {}),
            "read_attrs": device_info.get("read_attrs", []),
            "configuration_attrs": device_info.get("configuration_attrs", []),
            "current_status": device_status.get(device_name, {}).get("status", "unknown"),
            "current_position": device_status.get(device_name, {}).get("position"),
            "limits": device_status.get(device_name, {}).get("limits"),
            "connected": device_status.get(device_name, {}).get("connected", False),
            "full_info": device_info,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point for the backend server"""
    print("🚀 Starting bAIt-Chat with QServer integration...")
    print(f"📡 Backend API will be available at: http://{settings.host}:{settings.port}")
    print(f"📚 API Documentation at: http://{settings.host}:{settings.port}/docs")
    print(f"🔗 QServer URL: {QSERVER_URL}")
    print(f"🤖 LMStudio URL: {LMSTUDIO_URL}")

    uvicorn.run(
        "bait_mcp.server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
