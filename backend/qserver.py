"""
QServer client for interacting with Bluesky Queue Server
Handles plan submission, queue management, and device/plan retrieval
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
import json
from config.settings import settings

logger = logging.getLogger(__name__)


class QServerClient:
    """Client for Bluesky Queue Server HTTP API"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.QSERVER_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        
    async def connect(self):
        """Initialize connection to QServer"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    self._connected = True
                    logger.info(f"Connected to QServer at {self.base_url}")
                else:
                    logger.warning(f"QServer returned status {response.status}")
        except Exception as e:
            logger.error(f"Failed to connect to QServer: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Close connection to QServer"""
        if self.session:
            await self.session.close()
            self._connected = False
            logger.info("Disconnected from QServer")
    
    def is_connected(self) -> bool:
        """Check if connected to QServer"""
        return self._connected
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieve available Ophyd devices from QServer
        Returns list of device configurations
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.get(f"{self.base_url}/devices/allowed") as response:
                if response.status == 200:
                    data = await response.json()
                    devices = data.get("devices", {})
                    
                    # Format device information
                    formatted_devices = []
                    for name, info in devices.items():
                        formatted_devices.append({
                            "name": name,
                            "type": info.get("device_class", "unknown"),
                            "description": info.get("description", ""),
                            "components": info.get("components", []),
                            "is_readable": info.get("is_readable", True),
                            "is_movable": info.get("is_movable", False)
                        })
                    
                    logger.info(f"Retrieved {len(formatted_devices)} devices")
                    return formatted_devices
                else:
                    logger.error(f"Failed to get devices: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching devices: {e}")
            return []
    
    async def get_plans(self) -> List[Dict[str, Any]]:
        """
        Retrieve available scan plans from QServer
        Returns list of plan definitions
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.get(f"{self.base_url}/plans/allowed") as response:
                if response.status == 200:
                    data = await response.json()
                    plans = data.get("plans", {})
                    
                    # Format plan information
                    formatted_plans = []
                    for name, info in plans.items():
                        formatted_plans.append({
                            "name": name,
                            "description": info.get("description", ""),
                            "parameters": info.get("parameters", []),
                            "module": info.get("module", ""),
                            "is_generator": info.get("is_generator", True)
                        })
                    
                    logger.info(f"Retrieved {len(formatted_plans)} plans")
                    return formatted_plans
                else:
                    logger.error(f"Failed to get plans: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching plans: {e}")
            return []
    
    async def get_plan_source(self, plan_name: str) -> Optional[str]:
        """
        Get source code for a specific plan
        Used for plan explanation feature
        """
        try:
            if not self._connected:
                await self.connect()
            
            # First get plan info to find module
            plans = await self.get_plans()
            plan_info = next((p for p in plans if p["name"] == plan_name), None)
            
            if not plan_info:
                logger.warning(f"Plan '{plan_name}' not found")
                return None
            
            # In a real implementation, this would fetch actual source
            # For now, return a template
            source_template = f"""
def {plan_name}({', '.join(plan_info.get('parameters', []))}):
    '''
    {plan_info.get('description', 'No description available')}
    
    Parameters:
    {chr(10).join([f'    - {param}' for param in plan_info.get('parameters', [])])}
    '''
    # Plan implementation
    yield from plan_stub()
"""
            return source_template
            
        except Exception as e:
            logger.error(f"Error fetching plan source: {e}")
            return None
    
    # Phase 1.5 Methods - Queue Management (placeholder implementations)
    
    async def submit_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a plan to QServer queue
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            # Validate plan structure
            if "name" not in plan:
                raise ValueError("Plan must have a 'name' field")
            
            # Add plan to queue
            payload = {
                "item": plan,
                "user": settings.DEFAULT_USER,
                "user_group": settings.DEFAULT_USER_GROUP
            }
            
            async with self.session.post(
                f"{self.base_url}/queue/item/add",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Plan '{plan['name']}' submitted successfully")
                    return data
                else:
                    error = await response.text()
                    logger.error(f"Failed to submit plan: {error}")
                    raise Exception(f"Plan submission failed: {error}")
                    
        except Exception as e:
            logger.error(f"Error submitting plan: {e}")
            raise
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status and items
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.get(f"{self.base_url}/queue/get") as response:
                if response.status == 200:
                    data = await response.json()
                    queue_info = {
                        "running_item": data.get("running_item"),
                        "plan_queue": data.get("items", []),
                        "queue_size": len(data.get("items", [])),
                        "running": data.get("running_item") is not None
                    }
                    return queue_info
                else:
                    logger.error(f"Failed to get queue: HTTP {response.status}")
                    return {"plan_queue": [], "queue_size": 0, "running": False}
                    
        except Exception as e:
            logger.error(f"Error fetching queue: {e}")
            return {"plan_queue": [], "queue_size": 0, "running": False}
    
    async def clear_queue(self) -> bool:
        """
        Clear all items from the queue
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.post(f"{self.base_url}/queue/clear") as response:
                if response.status == 200:
                    logger.info("Queue cleared successfully")
                    return True
                else:
                    logger.error(f"Failed to clear queue: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
            return False
    
    async def remove_queue_item(self, uid: str) -> bool:
        """
        Remove specific item from queue by UID
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            payload = {"uid": uid}
            async with self.session.post(
                f"{self.base_url}/queue/item/remove",
                json=payload
            ) as response:
                if response.status == 200:
                    logger.info(f"Item {uid} removed from queue")
                    return True
                else:
                    logger.error(f"Failed to remove item: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error removing queue item: {e}")
            return False
    
    async def pause_run_engine(self) -> bool:
        """
        Pause the RunEngine
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.post(f"{self.base_url}/re/pause") as response:
                if response.status == 200:
                    logger.info("RunEngine paused")
                    return True
                else:
                    logger.error(f"Failed to pause: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pausing RunEngine: {e}")
            return False
    
    async def resume_run_engine(self) -> bool:
        """
        Resume the RunEngine
        Phase 1.5 functionality
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.post(f"{self.base_url}/re/resume") as response:
                if response.status == 200:
                    logger.info("RunEngine resumed")
                    return True
                else:
                    logger.error(f"Failed to resume: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error resuming RunEngine: {e}")
            return False
    
    async def get_environment_status(self) -> Dict[str, Any]:
        """
        Get overall environment status
        """
        try:
            if not self._connected:
                await self.connect()
            
            async with self.session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"manager_state": "unknown", "re_state": "unknown"}
                    
        except Exception as e:
            logger.error(f"Error fetching status: {e}")
            return {"manager_state": "error", "re_state": "error"}