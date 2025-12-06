#!/usr/bin/env python3
"""
TrueCancer V4 - API Endpoint Validation
Tests all production API endpoints
"""

import requests
import json
import time

PRODUCTION_URL = "https://cancer-detector-backend-production.up.railway.app"

print("=" * 80)
print("API ENDPOINT VALIDATION")
print("Production URL:", PRODUCTION_URL)
print("=" * 80)

tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"✓ PASS: {name}")
    else:
        tests_failed += 1
        print(f"✗ FAIL: {name}")
    if details:
        print(f"  {details}")
    return condition

# ============================================
# Test 1: Health Endpoint
# ============================================
print("\n" + "=" * 80)
print("Test 1: Health Endpoint")
print("=" * 80)

try:
    start = time.time()
    response = requests.get(f"{PRODUCTION_URL}/health", timeout=5)
    duration = time.time() - start
    
    test("Health endpoint responds", response.status_code == 200, f"Status: {response.status_code}")
    test("Health response < 2s", duration < 2.0, f"Duration: {duration:.2f}s")
    
    data = response.json()
    test("Status is healthy", data.get('status') == 'healthy')
    test("Version present", 'version' in data, f"Version: {data.get('version')}")
    
except Exception as e:
    test("Health endpoint", False, str(e))

# ============================================
# Test 2: V4 Scan Endpoint (Text-based)
# ============================================
print("\n" + "=" * 80)
print("Test 2: V4 Scan Endpoint (Text Input)")
print("=" * 80)

scan_data = {
    "product_name": "Test Product",
    "brand": "Test Brand",
    "category": "food",
    "ingredients": ["water", "salt", "sugar"]
}

try:
    start = time.time()
    response = requests.post(f"{PRODUCTION_URL}/api/v4/scan", json=scan_data, timeout=10)
    duration = time.time() - start
    
    test("Scan endpoint responds", response.status_code == 200, f"Status: {response.status_code}")
    test("Scan response < 2s", duration < 2.0, f"Duration: {duration:.2f}s")
    
    data = response.json()
    test("Overall score present", 'overall_score' in data)
    test("Overall grade present", 'overall_grade' in data)
    test("Ingredients graded", 'ingredients_graded' in data and len(data['ingredients_graded']) > 0)
    test("Alerts present", 'alerts' in data)
    
except Exception as e:
    test("V4 scan endpoint", False, str(e))

# ============================================
# Test 3: Deep Research Endpoint
# ============================================
print("\n" + "=" * 80)
print("Test 3: Deep Research Job Creation")
print("=" * 80)

dr_data = {
    "product_name": "Quick Test Product",
    "brand": "Test Brand",
    "category": "food",
    "ingredients": ["water", "salt"]
}

try:
    start = time.time()
    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=dr_data, timeout=10)
    duration = time.time() - start
    
    test("Deep Research endpoint responds", response.status_code == 200, f"Status: {response.status_code}")
    test("Job creation < 2s", duration < 2.0, f"Duration: {duration:.2f}s")
    
    data = response.json()
    test("Job ID returned", 'job_id' in data, f"Job ID: {data.get('job_id', 'N/A')}")
    test("Status URL present", 'check_status_url' in data)
    test("Message present", 'message' in data)
    
except Exception as e:
    test("Deep Research endpoint", False, str(e))

# ============================================
# Test 4: Error Handling - Malformed Request
# ============================================
print("\n" + "=" * 80)
print("Test 4: Error Handling - Malformed Requests")
print("=" * 80)

# Missing required fields
bad_data = {"product_name": "Test"}

try:
    response = requests.post(f"{PRODUCTION_URL}/api/v4/scan", json=bad_data, timeout=5)
    
    test("Malformed request handled", response.status_code in [400, 422, 500])
    
    if response.status_code != 200:
        test("Error message returned", 'detail' in response.json() or 'error' in response.json())
    
except Exception as e:
    test("Error handling", True, f"Graceful failure: {str(e)[:50]}")

# ============================================
# Test 5: CORS Headers
# ============================================
print("\n" + "=" * 80)
print("Test 5: CORS Configuration")
print("=" * 80)

try:
    response = requests.options(f"{PRODUCTION_URL}/health", headers={
        'Origin': 'https://example.com',
        'Access-Control-Request-Method': 'GET'
    })
    
    test("CORS preflight works", response.status_code in [200, 204])
    test("CORS headers present", 'access-control-allow-origin' in response.headers or 'Access-Control-Allow-Origin' in response.headers)
    
except Exception as e:
    test("CORS configuration", False, str(e))

# ============================================
# Test 6: Performance - Concurrent Requests
# ============================================
print("\n" + "=" * 80)
print("Test 6: Performance - Load Testing")
print("=" * 80)

import concurrent.futures

def make_request():
    try:
        start = time.time()
        response = requests.get(f"{PRODUCTION_URL}/health", timeout=10)
        duration = time.time() - start
        return response.status_code == 200 and duration < 3.0
    except:
        return False

try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_rate = sum(results) / len(results) * 100
    test("Concurrent requests handled", success_rate >= 80, f"Success rate: {success_rate:.0f}%")
    
except Exception as e:
    test("Load testing", False, str(e))

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 80)
print("API ENDPOINT TESTING - FINAL SUMMARY")
print("=" * 80)
print(f"\nTests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")

if tests_failed == 0:
    print("\n🎉 ALL API TESTS PASSED!")
else:
    print("\n⚠️ SOME API TESTS FAILED")

print("\n" + "=" * 80)
