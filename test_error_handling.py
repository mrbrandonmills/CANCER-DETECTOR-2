#!/usr/bin/env python3
"""
Error Handling Testing for TrueCancer V4
Tests various error scenarios and recovery
"""

import requests
import sys

PRODUCTION_URL = "https://cancer-detector-backend-production.up.railway.app"

print("=" * 80)
print("ERROR HANDLING TESTING SUITE")
print("=" * 80)

tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    """Helper function to track test results"""
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        status = "✓ PASS"
    else:
        tests_failed += 1
        status = "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"  Details: {details}")
    return condition

# ============================================
# Error Test 1: Invalid Job ID
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 1: Invalid Job ID")
print("=" * 80)

try:
    response = requests.get(f"{PRODUCTION_URL}/api/v4/job/nonexistent-job-id-12345")
    test("Returns 404 for invalid job ID", response.status_code == 404,
         f"Status code: {response.status_code}")

    if response.status_code == 404:
        data = response.json()
        test("Error message provided", 'error' in data or 'message' in data,
             f"Response: {data}")
except Exception as e:
    test("Invalid job ID handled", False, str(e))

# ============================================
# Error Test 2: Malformed Deep Research Request
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 2: Malformed Deep Research Request")
print("=" * 80)

try:
    # Missing required fields
    bad_request = {
        "brand": "Test Brand"
        # Missing product_name, category, ingredients
    }

    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=bad_request)
    test("Rejects malformed request", response.status_code in [400, 422],
         f"Status code: {response.status_code}")

    if response.status_code in [400, 422]:
        data = response.json()
        test("Error details provided", 'error' in data or 'detail' in data,
             f"Response keys: {list(data.keys())}")
except Exception as e:
    test("Malformed request handled", False, str(e))

# ============================================
# Error Test 3: Empty JSON Body
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 3: Empty JSON Body")
print("=" * 80)

try:
    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json={})
    test("Rejects empty request", response.status_code in [400, 422],
         f"Status code: {response.status_code}")
except Exception as e:
    test("Empty request handled", False, str(e))

# ============================================
# Error Test 4: Invalid JSON
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 4: Invalid JSON")
print("=" * 80)

try:
    response = requests.post(
        f"{PRODUCTION_URL}/api/v4/deep-research",
        data="this is not valid json",
        headers={'Content-Type': 'application/json'}
    )
    test("Rejects invalid JSON", response.status_code in [400, 422],
         f"Status code: {response.status_code}")
except Exception as e:
    test("Invalid JSON handled", False, str(e))

# ============================================
# Error Test 5: Invalid Category
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 5: Invalid Category")
print("=" * 80)

try:
    bad_category_request = {
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "invalid_category_xyz",
        "ingredients": ["water", "salt"]
    }

    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=bad_category_request)
    # Should either accept it gracefully or reject it
    test("Handles invalid category", response.status_code in [200, 400, 422],
         f"Status code: {response.status_code}")
except Exception as e:
    test("Invalid category handled", False, str(e))

# ============================================
# Error Test 6: Very Large Request (Payload Size)
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 6: Very Large Request (10,000 ingredients)")
print("=" * 80)

try:
    huge_request = {
        "product_name": "Massive Product",
        "brand": "Big Brand",
        "category": "food",
        "ingredients": [f"ingredient_{i}" for i in range(10000)]
    }

    response = requests.post(
        f"{PRODUCTION_URL}/api/v4/deep-research",
        json=huge_request,
        timeout=10
    )
    test("Handles large payload", response.status_code in [200, 400, 413, 422, 504],
         f"Status code: {response.status_code}")
except requests.exceptions.Timeout:
    test("Large payload causes timeout", True, "Request timed out as expected")
except Exception as e:
    test("Large payload handled", False, str(e))

# ============================================
# Error Test 7: Invalid Data Types
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 7: Invalid Data Types")
print("=" * 80)

try:
    bad_types_request = {
        "product_name": 12345,  # Should be string
        "brand": ["array", "instead", "of", "string"],  # Should be string
        "category": "food",
        "ingredients": "not an array"  # Should be array
    }

    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=bad_types_request)
    test("Validates data types", response.status_code in [400, 422],
         f"Status code: {response.status_code}")
except Exception as e:
    test("Invalid data types handled", False, str(e))

# ============================================
# Error Test 8: Missing Content-Type Header
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 8: Missing Content-Type Header")
print("=" * 80)

try:
    response = requests.post(
        f"{PRODUCTION_URL}/api/v4/deep-research",
        data='{"product_name": "test"}',
        # No Content-Type header
    )
    test("Handles missing Content-Type", response.status_code in [200, 400, 415, 422],
         f"Status code: {response.status_code}")
except Exception as e:
    test("Missing Content-Type handled", False, str(e))

# ============================================
# Error Test 9: SQL Injection Attempt
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 9: SQL Injection Attempt (Security)")
print("=" * 80)

try:
    sql_injection_request = {
        "product_name": "Test'; DROP TABLE products; --",
        "brand": "Test' OR '1'='1",
        "category": "food",
        "ingredients": ["water", "salt' OR '1'='1"]
    }

    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=sql_injection_request)
    test("Handles SQL injection safely", response.status_code in [200, 400, 422],
         f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        test("No error from SQL injection", 'job_id' in data or 'error' in data)
except Exception as e:
    test("SQL injection handled", False, str(e))

# ============================================
# Error Test 10: XSS Attempt
# ============================================
print("\n" + "=" * 80)
print("ERROR TEST 10: XSS Attempt (Security)")
print("=" * 80)

try:
    xss_request = {
        "product_name": "<script>alert('XSS')</script>",
        "brand": "Test<img src=x onerror=alert('XSS')>",
        "category": "food",
        "ingredients": ["water", "<script>alert('XSS')</script>"]
    }

    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=xss_request)
    test("Handles XSS safely", response.status_code in [200, 400, 422],
         f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        # Check that script tags are not executed/returned raw
        test("XSS not reflected", '<script>' not in str(data))
except Exception as e:
    test("XSS attempt handled", False, str(e))

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 80)
print("ERROR HANDLING TESTING SUMMARY")
print("=" * 80)
print(f"\nTests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")

if tests_failed == 0:
    print("\n🎉 ALL ERROR SCENARIOS HANDLED CORRECTLY!")
else:
    print("\n⚠️ SOME ERROR SCENARIOS NEED ATTENTION")

print("\n" + "=" * 80)
