"""
QServer integration tests
Tests for QServer client functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.qserver import QServerClient


class TestQServerClient:
    """Test QServer client functionality"""
    
    @pytest.fixture
    def qserver_client(self):
        """Create QServer client for testing"""
        return QServerClient(base_url="http://test-qserver:60610")
    
    @pytest.mark.asyncio
    async def test_connection(self, qserver_client):
        """Test QServer connection"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock successful connection
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            await qserver_client.connect()
            assert qserver_client.is_connected() == True
    
    @pytest.mark.asyncio
    async def test_failed_connection(self, qserver_client):
        """Test failed QServer connection"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock failed connection
            mock_session.return_value.__aenter__.return_value.get.side_effect = aiohttp.ClientError()
            
            await qserver_client.connect()
            assert qserver_client.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_get_devices(self, qserver_client):
        """Test getting devices from QServer"""
        mock_devices_response = {
            "devices": {
                "motor_x": {
                    "device_class": "EpicsMotor",
                    "description": "Sample X motor",
                    "is_readable": True,
                    "is_movable": True,
                    "components": ["position", "velocity"]
                },
                "pilatus": {
                    "device_class": "PilatusDetector", 
                    "description": "Pilatus 300K detector",
                    "is_readable": True,
                    "is_movable": False
                }
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock session and response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_devices_response
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Set client as connected
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            devices = await qserver_client.get_devices()
            
            assert len(devices) == 2
            assert devices[0]["name"] == "motor_x"
            assert devices[0]["type"] == "EpicsMotor"
            assert devices[0]["is_movable"] == True
            
            assert devices[1]["name"] == "pilatus"
            assert devices[1]["is_movable"] == False
    
    @pytest.mark.asyncio
    async def test_get_plans(self, qserver_client):
        """Test getting plans from QServer"""
        mock_plans_response = {
            "plans": {
                "scan": {
                    "description": "Continuous scan over motor range",
                    "parameters": ["detectors", "motor", "start", "stop", "num"],
                    "module": "bluesky.plans",
                    "is_generator": True
                },
                "count": {
                    "description": "Take repeated measurements",
                    "parameters": ["detectors", "num", "delay"],
                    "module": "bluesky.plans",
                    "is_generator": True
                }
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_plans_response
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            plans = await qserver_client.get_plans()
            
            assert len(plans) == 2
            assert plans[0]["name"] == "scan"
            assert "detectors" in plans[0]["parameters"]
            assert plans[1]["name"] == "count"
    
    @pytest.mark.asyncio
    async def test_get_plan_source(self, qserver_client):
        """Test getting plan source code"""
        qserver_client._connected = True
        
        with patch.object(qserver_client, 'get_plans') as mock_get_plans:
            mock_get_plans.return_value = [
                {
                    "name": "scan",
                    "description": "Continuous scan",
                    "parameters": ["detectors", "motor", "start", "stop", "num"]
                }
            ]
            
            source = await qserver_client.get_plan_source("scan")
            
            assert source is not None
            assert "def scan(" in source
            assert "detectors" in source
    
    @pytest.mark.asyncio
    async def test_submit_plan(self, qserver_client):
        """Test plan submission (Phase 1.5)"""
        mock_submit_response = {
            "success": True,
            "msg": "Plan added to queue",
            "qsize": 1,
            "item": {
                "name": "scan",
                "args": [["pilatus"], "motor_x", 0, 5, 51],
                "uid": "test-uid-123"
            }
        }
        
        test_plan = {
            "name": "scan",
            "args": [["pilatus"], "motor_x", 0, 5, 51],
            "kwargs": {}
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_submit_response
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            result = await qserver_client.submit_plan(test_plan)
            
            assert result["success"] == True
            assert result["qsize"] == 1
    
    @pytest.mark.asyncio
    async def test_get_queue_status(self, qserver_client):
        """Test getting queue status"""
        mock_queue_response = {
            "success": True,
            "msg": "",
            "items": [
                {
                    "name": "scan",
                    "args": [["pilatus"], "motor_x", 0, 5, 51],
                    "uid": "item-1"
                }
            ],
            "running_item": {
                "name": "count",
                "args": [["pilatus"], 10],
                "uid": "running-item"
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_queue_response
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            status = await qserver_client.get_queue_status()
            
            assert status["queue_size"] == 1
            assert status["running"] == True
            assert status["running_item"]["name"] == "count"
    
    @pytest.mark.asyncio
    async def test_clear_queue(self, qserver_client):
        """Test clearing the queue"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            result = await qserver_client.clear_queue()
            
            assert result == True
    
    @pytest.mark.asyncio
    async def test_remove_queue_item(self, qserver_client):
        """Test removing item from queue"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            result = await qserver_client.remove_queue_item("test-uid")
            
            assert result == True
    
    @pytest.mark.asyncio
    async def test_pause_run_engine(self, qserver_client):
        """Test pausing RunEngine"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            result = await qserver_client.pause_run_engine()
            
            assert result == True
    
    @pytest.mark.asyncio
    async def test_resume_run_engine(self, qserver_client):
        """Test resuming RunEngine"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            result = await qserver_client.resume_run_engine()
            
            assert result == True
    
    @pytest.mark.asyncio
    async def test_error_handling(self, qserver_client):
        """Test error handling in QServer client"""
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock HTTP error
            mock_session.return_value.__aenter__.return_value.get.side_effect = aiohttp.ClientError("Network error")
            
            qserver_client._connected = True
            qserver_client.session = mock_session.return_value.__aenter__.return_value
            
            devices = await qserver_client.get_devices()
            plans = await qserver_client.get_plans()
            
            # Should return empty lists on error
            assert devices == []
            assert plans == []


@pytest.mark.integration
class TestQServerIntegration:
    """Integration tests requiring actual QServer"""
    
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests disabled"
    )
    @pytest.mark.asyncio
    async def test_real_qserver_connection(self):
        """Test connection to real QServer (if available)"""
        qserver_url = os.getenv("QSERVER_URL", "http://localhost:60610")
        client = QServerClient(qserver_url)
        
        await client.connect()
        
        if client.is_connected():
            # Test basic operations
            devices = await client.get_devices()
            plans = await client.get_plans()
            
            assert isinstance(devices, list)
            assert isinstance(plans, list)
        
        await client.disconnect()