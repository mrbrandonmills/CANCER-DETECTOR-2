"""
Test Redis job persistence functionality
Run this to verify Redis integration works correctly
"""

import json
import redis
import os
from datetime import datetime

# Test Redis connection
def test_redis_connection():
    """Test that Redis connection works"""
    print("Testing Redis connection...")
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print(f"✅ Redis connected: {redis_url}")
        return client
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None

# Test job persistence
def test_job_persistence(client):
    """Test saving and retrieving jobs from Redis"""
    if not client:
        print("⚠️ Skipping persistence test (no Redis)")
        return False

    print("\nTesting job persistence...")

    # Create test job
    job_id = "test-123"
    job_data = {
        "job_id": job_id,
        "status": "processing",
        "progress": 50,
        "current_step": "Testing Redis storage...",
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
        "completed_at": None
    }

    # Save to Redis with 24-hour expiration
    try:
        client.setex(
            f"job:{job_id}",
            86400,  # 24 hours
            json.dumps(job_data)
        )
        print(f"✅ Job saved to Redis: {job_id}")
    except Exception as e:
        print(f"❌ Failed to save job: {e}")
        return False

    # Retrieve from Redis
    try:
        retrieved_json = client.get(f"job:{job_id}")
        if retrieved_json:
            retrieved = json.loads(retrieved_json)
            print(f"✅ Job retrieved from Redis")
            print(f"   Status: {retrieved['status']}")
            print(f"   Progress: {retrieved['progress']}%")
            print(f"   Step: {retrieved['current_step']}")

            # Verify data matches
            assert retrieved["status"] == job_data["status"], "Status mismatch"
            assert retrieved["progress"] == job_data["progress"], "Progress mismatch"
            print(f"✅ Data integrity verified")

            # Clean up test job
            client.delete(f"job:{job_id}")
            print(f"✅ Test job cleaned up")

            return True
        else:
            print(f"❌ Job not found in Redis")
            return False
    except Exception as e:
        print(f"❌ Failed to retrieve job: {e}")
        return False

# Test TTL expiration
def test_ttl(client):
    """Test that TTL is set correctly"""
    if not client:
        print("⚠️ Skipping TTL test (no Redis)")
        return False

    print("\nTesting TTL expiration...")

    job_id = "test-ttl-456"
    job_data = {"test": "data"}

    # Save with 24-hour TTL
    client.setex(f"job:{job_id}", 86400, json.dumps(job_data))

    # Check TTL
    ttl = client.ttl(f"job:{job_id}")
    print(f"✅ TTL set: {ttl} seconds (~{ttl/3600:.1f} hours)")

    # Verify TTL is approximately 24 hours
    if 86000 < ttl <= 86400:
        print(f"✅ TTL is correct (24 hours)")
        client.delete(f"job:{job_id}")
        return True
    else:
        print(f"❌ TTL is incorrect: expected ~86400, got {ttl}")
        client.delete(f"job:{job_id}")
        return False

# Test update operation
def test_job_update(client):
    """Test updating job progress"""
    if not client:
        print("⚠️ Skipping update test (no Redis)")
        return False

    print("\nTesting job updates...")

    job_id = "test-update-789"

    # Create initial job
    job_data = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "current_step": "Starting..."
    }
    client.setex(f"job:{job_id}", 86400, json.dumps(job_data))
    print(f"✅ Initial job created (progress: 0%)")

    # Update progress
    job_data["progress"] = 50
    job_data["current_step"] = "Halfway done..."
    client.setex(f"job:{job_id}", 86400, json.dumps(job_data))

    # Retrieve and verify
    retrieved = json.loads(client.get(f"job:{job_id}"))
    if retrieved["progress"] == 50:
        print(f"✅ Job updated (progress: 50%)")
    else:
        print(f"❌ Update failed")
        client.delete(f"job:{job_id}")
        return False

    # Complete job
    job_data["status"] = "completed"
    job_data["progress"] = 100
    job_data["current_step"] = "Complete"
    job_data["completed_at"] = datetime.utcnow().isoformat()
    client.setex(f"job:{job_id}", 86400, json.dumps(job_data))

    # Retrieve and verify
    retrieved = json.loads(client.get(f"job:{job_id}"))
    if retrieved["status"] == "completed" and retrieved["progress"] == 100:
        print(f"✅ Job completed (progress: 100%)")
        client.delete(f"job:{job_id}")
        return True
    else:
        print(f"❌ Completion failed")
        client.delete(f"job:{job_id}")
        return False

# Run all tests
if __name__ == "__main__":
    print("=" * 60)
    print("REDIS JOB PERSISTENCE TEST SUITE")
    print("=" * 60)

    # Connect to Redis
    client = test_redis_connection()

    # Run tests
    results = {
        "connection": client is not None,
        "persistence": test_job_persistence(client),
        "ttl": test_ttl(client),
        "updates": test_job_update(client)
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")

    # Overall result
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Redis persistence is working!")
    else:
        print("❌ SOME TESTS FAILED - Check Redis configuration")
        if not results["connection"]:
            print("\nTo fix:")
            print("1. Install Redis: brew install redis (Mac) or apt install redis (Linux)")
            print("2. Start Redis: redis-server")
            print("3. Or set REDIS_URL environment variable for remote Redis")
    print("=" * 60)
