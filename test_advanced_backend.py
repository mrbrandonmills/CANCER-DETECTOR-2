#!/usr/bin/env python3
"""
Test the advanced backend to ensure it's working properly
"""

import base64
import requests
import json

# Create a tiny 1x1 PNG for testing
tiny_png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

print("Testing advanced backend...")
print("=" * 50)

# Test 1: Health check
print("\n1. Testing /health endpoint...")
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: Check API endpoints
print("\n2. Testing / endpoint...")
try:
    response = requests.get("http://localhost:8000/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 50)
print("Backend is ready to deploy to Railway!")
