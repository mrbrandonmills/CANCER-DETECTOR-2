#!/usr/bin/env python3
"""
Performance Testing for TrueCancer V4
Tests response times and resource usage
"""

import time
import requests
import sys
sys.path.append('.')
from main import calculate_v4_score

PRODUCTION_URL = "https://cancer-detector-backend-production.up.railway.app"

print("=" * 80)
print("PERFORMANCE TESTING SUITE")
print("=" * 80)

# ============================================
# Test 1: V4 Local Scoring Performance
# ============================================
print("\n" + "=" * 80)
print("TEST 1: V4 Local Scoring Performance")
print("=" * 80)

test_data = {
    "product_name": "Cheez-It Original",
    "brand": "Kellogg's",
    "category": "food",
    "ingredients": [
        "enriched flour", "vegetable oil", "cheese", "salt", "paprika", "yeast",
        "tbhq", "yellow 5", "yellow 6", "high fructose corn syrup", "palm oil"
    ]
}

# Run 10 iterations to get average
times = []
for i in range(10):
    start = time.time()
    result = calculate_v4_score(test_data)
    end = time.time()
    times.append(end - start)

avg_time = sum(times) / len(times)
min_time = min(times)
max_time = max(times)

print(f"Average time: {avg_time*1000:.2f}ms")
print(f"Min time: {min_time*1000:.2f}ms")
print(f"Max time: {max_time*1000:.2f}ms")
print(f"✓ Target: < 3000ms - {'PASS' if avg_time < 3 else 'FAIL'}")

# ============================================
# Test 2: Health Endpoint Response Time
# ============================================
print("\n" + "=" * 80)
print("TEST 2: Health Endpoint Response Time")
print("=" * 80)

try:
    times = []
    for i in range(5):
        start = time.time()
        response = requests.get(f"{PRODUCTION_URL}/health")
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    print(f"Average response time: {avg_time*1000:.2f}ms")
    print(f"✓ Target: < 500ms - {'PASS' if avg_time < 0.5 else 'FAIL'}")
except Exception as e:
    print(f"✗ FAIL: {e}")

# ============================================
# Test 3: Deep Research Job Creation Time
# ============================================
print("\n" + "=" * 80)
print("TEST 3: Deep Research Job Creation Time")
print("=" * 80)

try:
    dr_request = {
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "food",
        "ingredients": ["water", "salt"]
    }

    start = time.time()
    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=dr_request)
    end = time.time()

    response_time = end - start
    print(f"Job creation time: {response_time*1000:.2f}ms")
    print(f"✓ Target: < 1000ms - {'PASS' if response_time < 1 else 'FAIL'}")
except Exception as e:
    print(f"✗ FAIL: {e}")

# ============================================
# Test 4: Job Status Check Performance
# ============================================
print("\n" + "=" * 80)
print("TEST 4: Job Status Check Performance")
print("=" * 80)

try:
    # Create a job first
    dr_request = {
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "food",
        "ingredients": ["water", "salt"]
    }
    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=dr_request)
    job_id = response.json().get('job_id')

    if job_id:
        times = []
        for i in range(5):
            start = time.time()
            response = requests.get(f"{PRODUCTION_URL}/api/v4/job/{job_id}")
            end = time.time()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        print(f"Average status check time: {avg_time*1000:.2f}ms")
        print(f"✓ Target: < 100ms - {'PASS' if avg_time < 0.1 else 'FAIL'}")
    else:
        print("✗ FAIL: Could not create test job")
except Exception as e:
    print(f"✗ FAIL: {e}")

# ============================================
# Test 5: Concurrent Request Handling
# ============================================
print("\n" + "=" * 80)
print("TEST 5: Concurrent Request Handling (Stress Test)")
print("=" * 80)

try:
    import concurrent.futures

    def make_health_check():
        start = time.time()
        response = requests.get(f"{PRODUCTION_URL}/health")
        end = time.time()
        return end - start, response.status_code

    # Send 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_health_check) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    times = [r[0] for r in results]
    status_codes = [r[1] for r in results]

    avg_time = sum(times) / len(times)
    all_success = all(code == 200 for code in status_codes)

    print(f"Concurrent requests: 10")
    print(f"Average response time: {avg_time*1000:.2f}ms")
    print(f"Success rate: {sum(1 for c in status_codes if c == 200)}/10")
    print(f"✓ All requests successful: {'PASS' if all_success else 'FAIL'}")
except Exception as e:
    print(f"✗ FAIL: {e}")

# ============================================
# Test 6: Memory Usage (Approximation)
# ============================================
print("\n" + "=" * 80)
print("TEST 6: Memory Usage Test")
print("=" * 80)

try:
    import psutil
    import os

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB

    # Run 100 scoring operations
    for i in range(100):
        result = calculate_v4_score(test_data)

    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_increase = mem_after - mem_before

    print(f"Memory before: {mem_before:.2f} MB")
    print(f"Memory after: {mem_after:.2f} MB")
    print(f"Memory increase: {mem_increase:.2f} MB")
    print(f"✓ Target: < 50MB increase - {'PASS' if mem_increase < 50 else 'FAIL'}")
except ImportError:
    print("⚠️ psutil not installed - skipping memory test")
    print("Install with: pip install psutil")
except Exception as e:
    print(f"✗ FAIL: {e}")

print("\n" + "=" * 80)
print("PERFORMANCE TESTING COMPLETE")
print("=" * 80)
