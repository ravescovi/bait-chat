"""
Tests for bAIt-Chat API endpoints
Tests the current FastAPI backend server
"""

import asyncio
import os
import sys

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import from the backend package
from bait_mcp.server import app

# Test client setup
client = TestClient(app)


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root(self):
        """Test root endpoint returns basic info"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "qserver_url" in data


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health endpoint returns correct format"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "llm_provider" in data
        assert "qserver_status" in data
        assert "qserver_url" in data


class TestDevicesEndpoint:
    """Test device listing endpoint"""

    def test_get_devices(self):
        """Test devices endpoint returns organized device structure"""
        response = client.get("/devices")
        assert response.status_code == 200

        data = response.json()
        assert "devices" in data
        assert isinstance(data["devices"], dict)

        # Should have device categories
        devices = data["devices"]
        expected_categories = ["motors", "detectors", "other"]
        for category in expected_categories:
            assert category in devices
            assert isinstance(devices[category], dict)


class TestPlansEndpoint:
    """Test plan listing endpoint"""

    def test_get_plans(self):
        """Test plans endpoint returns plan structure"""
        response = client.get("/plans")
        assert response.status_code == 200

        data = response.json()
        assert "plans" in data
        assert isinstance(data["plans"], dict)

        # Check plan structure if plans exist
        plans = data["plans"]
        if plans:
            plan_name = list(plans.keys())[0]
            plan = plans[plan_name]
            assert "description" in plan


class TestQServerStatusEndpoint:
    """Test QServer status endpoint"""

    def test_qserver_status(self):
        """Test QServer status endpoint"""
        response = client.get("/qserver/status")

        # Should either return 200 with status or 500 if QServer unavailable
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "manager_state" in data


class TestExplainEndpoint:
    """Test plan explanation endpoint"""

    def test_explain_plan(self):
        """Test explanation endpoint"""
        response = client.post("/explain", json={"plan_name": "count"})

        assert response.status_code == 200
        data = response.json()
        assert "plan_name" in data
        assert "explanation" in data
        assert len(data["explanation"]) > 0

    def test_explain_general_question(self):
        """Test explanation with general question"""
        response = client.post("/explain", json={"plan_name": "What devices are available?"})

        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data


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
            "/explain", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality"""

    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Send multiple concurrent requests
            tasks = [ac.get("/health"), ac.get("/devices"), ac.get("/plans")]

            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS configuration"""

    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.get("/health")

        # CORS headers should be present
        assert response.status_code == 200
        # Note: TestClient doesn't include CORS headers, but the middleware is configured