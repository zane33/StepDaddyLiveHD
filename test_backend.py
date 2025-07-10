#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""
import os
import asyncio
import httpx
import pytest
from StepDaddyLiveHD.step_daddy import StepDaddy
from StepDaddyLiveHD.backend import fastapi_app
from fastapi.testclient import TestClient

client = TestClient(fastapi_app)

# Use the backend port for testing
base_url = os.environ.get("API_URL", "http://localhost:8005")

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok" 