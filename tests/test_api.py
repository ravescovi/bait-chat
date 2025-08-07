"""
API endpoint tests for bAIt-Chat
Tests for FastAPI endpoints and functionality
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.main import app


# Test client setup
client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns correct format"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert isinstance(data["services"], dict)


class TestDevicesEndpoint:
    """Test device listing endpoint"""
    
    def test_get_devices(self):
        """Test devices endpoint returns list"""
        response = client.get("/devices")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check device structure if devices exist
        if data:
            device = data[0]
            assert "name" in device
            assert "type" in device
            assert "is_readable" in device
            assert "is_movable" in device


class TestPlansEndpoint:
    """Test plan listing endpoint"""
    
    def test_get_plans(self):
        """Test plans endpoint returns list"""
        response = client.get("/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check plan structure if plans exist
        if data:
            plan = data[0]
            assert "name" in plan
            assert "description" in plan
            assert "parameters" in plan


class TestLastScanEndpoint:
    """Test last scan endpoint"""
    
    def test_get_last_scan(self):
        """Test last scan endpoint returns scan data"""
        response = client.get("/last_scan")
        
        # Should either return 200 with scan data or 404 if no scans
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "scan_id" in data
            assert "timestamp" in data
            assert "plan_name" in data
            assert "exit_status" in data


class TestExplainEndpoint:
    """Test plan explanation endpoint"""
    
    def test_explain_with_plan_name(self):
        """Test explanation with predefined plan name"""
        response = client.post("/explain", json={
            "plan_name": "scan"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert "timestamp" in data
        assert len(data["explanation"]) > 0
    
    def test_explain_with_source_code(self):
        """Test explanation with source code"""
        test_code = """
def test_plan():
    '''A simple test plan'''
    yield from count([det], num=10)
"""
        
        response = client.post("/explain", json={
            "plan_source": test_code
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
    
    def test_explain_missing_input(self):
        """Test explanation with missing input"""
        response = client.post("/explain", json={})
        
        assert response.status_code == 422  # Validation error


class TestSearchEndpoint:
    """Test knowledge base search endpoint"""
    
    def test_search_with_query(self):
        """Test search with query parameter"""
        response = client.get("/search?query=motor&limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "motor"
        assert isinstance(data["results"], list)
    
    def test_search_without_query(self):
        """Test search without query parameter"""
        response = client.get("/search")
        assert response.status_code == 422  # Missing required parameter


class TestPhase15Placeholders:
    """Test Phase 1.5 placeholder endpoints"""
    
    def test_submit_plan_placeholder(self):
        """Test plan submission placeholder"""
        response = client.post("/submit_plan", json={
            "name": "scan",
            "args": ["detector", "motor", 0, 5, 10]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"
    
    def test_queue_status_placeholder(self):
        """Test queue status placeholder"""
        response = client.get("/queue")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"
    
    def test_clear_queue_placeholder(self):
        """Test clear queue placeholder"""
        response = client.delete("/queue/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"
    
    def test_remove_queue_item_placeholder(self):
        """Test remove queue item placeholder"""
        response = client.delete("/queue/item/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"
    
    def test_pause_re_placeholder(self):
        """Test pause RunEngine placeholder"""
        response = client.post("/re/pause")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"
    
    def test_resume_re_placeholder(self):
        """Test resume RunEngine placeholder"""
        response = client.post("/re/resume")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "not_implemented"


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality"""
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Send multiple concurrent requests
            tasks = [
                ac.get("/health"),
                ac.get("/devices"),
                ac.get("/plans"),
                ac.get("/search?query=test")
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_endpoint(self):
        """Test 404 for invalid endpoint"""
        response = client.get("/invalid_endpoint")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test 405 for invalid HTTP method"""
        response = client.delete("/health")
        assert response.status_code == 405
    
    def test_malformed_json(self):
        """Test 422 for malformed JSON"""
        response = client.post(
            "/explain",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


# Fixtures for integration tests
@pytest.fixture
def mock_qserver_response():
    """Mock QServer response data"""
    return {
        "devices": [
            {
                "name": "motor_x",
                "type": "motor",
                "description": "Sample X position motor",
                "is_readable": True,
                "is_movable": True,
                "metadata": {"units": "mm"}
            }
        ],
        "plans": [
            {
                "name": "scan",
                "description": "Continuous scan",
                "parameters": [
                    {"name": "detectors", "type": "list", "required": True},
                    {"name": "motor", "type": "str", "required": True}
                ]
            }
        ]
    }


@pytest.fixture
def mock_scan_data():
    """Mock scan result data"""
    return {
        "scan_id": "test-scan-123",
        "uid": "test123",
        "timestamp": "2024-01-15T10:30:00",
        "plan_name": "scan",
        "exit_status": "completed",
        "duration": 125.4,
        "motors": ["motor_x"],
        "detectors": ["pilatus"]
    }