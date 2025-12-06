# Redis Job Persistence Setup Guide

## Overview

TrueCancer V4 now uses **Redis** for job persistence to prevent Deep Research jobs from being lost when Railway restarts the server.

### Key Features
- ✅ Jobs persist across server restarts
- ✅ Automatic 24-hour expiration (TTL)
- ✅ Graceful fallback to in-memory storage if Redis unavailable
- ✅ Zero breaking changes - existing code still works

---

## Local Development

### Option 1: Install Redis Locally

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Windows:**
```bash
# Use WSL or Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Option 2: Use Docker
```bash
docker run -d -p 6379:6379 --name truecancer-redis redis:7-alpine
```

### Test Redis Connection
```bash
cd /Volumes/Super\ Mastery/CANCER\ DETECTOR\ VERSION\ 2\ REBUILD
python test_redis_jobs.py
```

Expected output:
```
✅ Redis connected: redis://localhost:6379
✅ Job saved to Redis: test-123
✅ Job retrieved from Redis
✅ Data integrity verified
✅ ALL TESTS PASSED
```

---

## Railway Deployment

### Step 1: Add Redis Plugin

1. Go to your Railway project dashboard
2. Click **"+ New"** → **"Database"** → **"Add Redis"**
3. Railway will automatically:
   - Provision a Redis instance
   - Create `REDIS_URL` environment variable
   - Connect it to your backend service

### Step 2: Verify Environment Variable

The backend automatically reads `REDIS_URL`:

```python
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
```

Railway sets this to:
```
redis://default:password@redis.railway.internal:6379
```

### Step 3: Deploy Updated Code

```bash
git add .
git commit -m "Add Redis job persistence"
git push
```

Railway will:
1. Install `redis==5.0.1` from `requirements.txt`
2. Connect to Redis automatically
3. Start persisting jobs

### Step 4: Verify Deployment

Check Railway logs for:
```
✅ Redis connected: redis://default:****@redis.railway.internal:6379
```

If you see this instead:
```
⚠️ Redis connection failed: [error]
Falling back to in-memory storage
```

Then Redis is not connected. Check:
1. Redis add-on is provisioned
2. `REDIS_URL` environment variable exists
3. Redis service is running

---

## Architecture

### How It Works

```
┌─────────────────────────────────────────────┐
│         TrueCancer Backend (FastAPI)        │
│                                             │
│  POST /api/v4/deep-research                 │
│         ↓                                   │
│  1. Create job with unique ID               │
│  2. Save to Redis (24hr TTL)                │
│  3. Start background processing             │
│  4. Return job_id to client                 │
└─────────────────────────────────────────────┘
                    ↓
         ┌──────────────────┐
         │  Redis Database  │
         │                  │
         │  job:uuid-123 ──→│  {status, progress, result}
         │  job:uuid-456 ──→│  {status, progress, result}
         │  job:uuid-789 ──→│  {status, progress, result}
         │                  │
         │  Auto-expires    │
         │  after 24 hours  │
         └──────────────────┘
                    ↓
         GET /api/v4/job/{job_id}
         ← Retrieve job from Redis
```

### Data Structure

**Job stored in Redis:**
```json
{
  "job_id": "uuid-123",
  "status": "processing",
  "progress": 50,
  "current_step": "Investigating supply chain...",
  "created_at": "2025-12-05T10:30:00Z",
  "completed_at": null,
  "result": null,
  "error": null
}
```

**Redis key format:**
```
job:{uuid} → JSON string (TTL: 86400 seconds = 24 hours)
```

### Fallback Behavior

If Redis is unavailable, the system automatically falls back to in-memory storage:

```python
redis_client = None  # Redis failed to connect

# save_job_to_redis() automatically uses DEEP_RESEARCH_JOBS dict
# Jobs work normally, but are lost on restart
```

---

## API Endpoints

### Start Deep Research
```http
POST /api/v4/deep-research
Content-Type: application/json

{
  "product_name": "Dove Body Wash",
  "brand": "Dove",
  "category": "cosmetics",
  "ingredients": ["Water", "Sodium Laureth Sulfate", "Fragrance"]
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Deep research initiated.",
  "check_status_url": "/api/v4/job/550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Job Status
```http
GET /api/v4/job/550e8400-e29b-41d4-a716-446655440000
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 50,
  "current_step": "Investigating supply chain...",
  "created_at": "2025-12-05T10:30:00Z",
  "result": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "created_at": "2025-12-05T10:30:00Z",
  "completed_at": "2025-12-05T10:35:00Z",
  "result": {
    "product_name": "Dove Body Wash",
    "brand": "Dove",
    "report": { ... },
    "full_report": "..."
  }
}
```

### Admin Cleanup (Optional)
```http
DELETE /api/v4/admin/cleanup-jobs
```

Returns info about automatic TTL-based cleanup.

---

## Code Changes Summary

### Files Modified

1. **`requirements.txt`**
   - Added: `redis==5.0.1`

2. **`main.py`**
   - Added Redis client setup (lines 43-55)
   - Added Redis helper functions (lines 1667-1723)
   - Updated `process_deep_research()` to use Redis
   - Updated `/api/v4/deep-research` endpoint
   - Updated `/api/v4/job/{job_id}` endpoint
   - Added `/api/v4/admin/cleanup-jobs` endpoint

3. **`test_redis_jobs.py`** (NEW)
   - Test suite for Redis persistence
   - Verifies connection, save, retrieve, update, TTL

4. **`REDIS_SETUP.md`** (NEW)
   - This documentation file

---

## Redis Helper Functions

### `save_job_to_redis(job_id, job_data)`
Saves job to Redis with 24-hour TTL. Falls back to in-memory if Redis unavailable.

### `get_job_from_redis(job_id)`
Retrieves job from Redis or in-memory fallback. Returns `None` if not found.

### `update_job_progress(job_id, progress, current_step)`
Updates job progress and current step in Redis.

### `complete_job(job_id, result)`
Marks job as completed with final report.

### `fail_job(job_id, error)`
Marks job as failed with error message.

---

## Monitoring

### Check Redis Status in Logs

**Successful connection:**
```
✅ Redis connected: redis://default:****@redis.railway.internal:6379
```

**Failed connection (fallback):**
```
⚠️ Redis connection failed: Connection refused
Falling back to in-memory storage (jobs will be lost on restart)
```

### Railway Redis Dashboard

1. Go to Railway project
2. Click Redis service
3. View:
   - **Metrics**: Memory usage, connections
   - **Logs**: Redis server logs
   - **Variables**: `REDIS_URL` value

---

## Troubleshooting

### Issue: "Redis connection failed"

**Cause:** Redis service not running or `REDIS_URL` not set

**Fix:**
```bash
# Local development
brew services start redis

# Railway
1. Add Redis database from dashboard
2. Verify REDIS_URL exists in environment variables
3. Redeploy backend service
```

### Issue: "Job not found" after restart

**Cause:** Redis not connected, using in-memory fallback

**Fix:**
1. Check logs for Redis connection status
2. Ensure `REDIS_URL` environment variable is set
3. Restart service after adding Redis

### Issue: Jobs expire too quickly

**Cause:** TTL is set to 24 hours

**Fix:**
Change TTL in `save_job_to_redis()`:
```python
redis_client.setex(
    f"job:{job_id}",
    172800,  # 48 hours instead of 24
    json.dumps(job_data)
)
```

---

## Performance Considerations

### Memory Usage
- Each job ~5-50 KB (depending on report size)
- 1000 jobs = ~50 MB
- Redis auto-expires jobs after 24 hours

### Redis Limits (Railway Free Tier)
- 25 MB storage (500+ jobs)
- Auto-eviction if exceeded
- Upgrade to Pro for unlimited storage

### Optimization Tips
1. Keep job TTL at 24 hours (86400 seconds)
2. Clean up completed jobs client-side
3. Consider compressing large reports
4. Monitor Redis memory usage in Railway dashboard

---

## Next Steps

1. ✅ Deploy to Railway with Redis add-on
2. ✅ Test job persistence across restarts
3. ⏳ Monitor Redis metrics in production
4. ⏳ Consider Redis Cluster for high availability (future)
5. ⏳ Add job analytics/monitoring dashboard (future)

---

## Support

**Issues?**
- Check Railway logs for Redis connection errors
- Run `python test_redis_jobs.py` locally
- Verify `REDIS_URL` environment variable
- Ensure Redis add-on is provisioned in Railway

**Questions?**
- Redis TTL: 24 hours (auto-cleanup)
- Fallback: In-memory storage (cleared on restart)
- Storage limit: Railway Free = 25 MB, Pro = Unlimited
