# Redis Deployment Checklist for Railway

## Pre-Deployment

- [x] Redis dependencies added to `requirements.txt`
- [x] Redis client setup in `main.py`
- [x] Helper functions created
- [x] Job endpoints updated
- [x] Test suite created
- [x] Documentation written

## Railway Setup

### Step 1: Add Redis Database
- [ ] Log into Railway dashboard
- [ ] Navigate to TrueCancer project
- [ ] Click **"+ New"** button
- [ ] Select **"Database"** → **"Add Redis"**
- [ ] Wait for provisioning (1-2 minutes)
- [ ] Verify `REDIS_URL` appears in environment variables

### Step 2: Deploy Backend
- [ ] Commit changes to git:
  ```bash
  cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
  git add .
  git commit -m "feat: Add Redis job persistence to prevent job loss on restart"
  git push
  ```
- [ ] Wait for Railway deployment to complete
- [ ] Check deployment logs for success

### Step 3: Verify Redis Connection
- [ ] Open Railway deployment logs
- [ ] Look for: `✅ Redis connected: redis://...`
- [ ] If you see fallback warning, troubleshoot below

### Step 4: Test Deep Research
- [ ] Start a Deep Research job via API:
  ```bash
  curl -X POST https://your-app.railway.app/api/v4/deep-research \
    -H "Content-Type: application/json" \
    -d '{
      "product_name": "Test Product",
      "brand": "Test Brand",
      "category": "food",
      "ingredients": ["Water", "Sugar"]
    }'
  ```
- [ ] Note the `job_id` in response
- [ ] Check job status:
  ```bash
  curl https://your-app.railway.app/api/v4/job/{job_id}
  ```
- [ ] Verify progress updates correctly

### Step 5: Test Persistence (Critical!)
- [ ] Start a Deep Research job
- [ ] Wait for it to reach 50% progress
- [ ] Restart Railway service:
  - Go to Railway dashboard
  - Click on backend service
  - Click **"Deploy"** → **"Restart"**
- [ ] After restart, check job status again
- [ ] ✅ **SUCCESS**: Job still exists with progress intact
- [ ] ❌ **FAILURE**: Job not found (Redis not connected)

## Troubleshooting

### Issue: Redis Connection Failed

**Symptoms:**
```
⚠️ Redis connection failed: Connection refused
Falling back to in-memory storage
```

**Solutions:**
1. Verify Redis add-on exists in Railway project
2. Check `REDIS_URL` environment variable:
   - Go to backend service settings
   - Navigate to "Variables" tab
   - Look for `REDIS_URL`
   - Should be: `redis://default:***@redis.railway.internal:6379`
3. Ensure Redis and backend are in same project
4. Redeploy backend service
5. Check Redis service logs for errors

### Issue: Job Not Found After Restart

**Symptoms:**
```
GET /api/v4/job/{job_id} → 404 Not Found
```

**Cause:** Redis not connected, using in-memory fallback

**Solutions:**
1. Check logs for Redis connection status
2. Follow "Redis Connection Failed" troubleshooting above
3. Verify Redis add-on is running (check Railway dashboard)

### Issue: Jobs Expire Too Quickly

**Current TTL:** 24 hours

**To change:**
Edit `main.py` line ~1671:
```python
redis_client.setex(
    f"job:{job_id}",
    172800,  # 48 hours (86400 * 2)
    json.dumps(job_data)
)
```

## Post-Deployment Verification

### Health Checks
- [ ] Backend is healthy: `GET /health`
- [ ] Deep Research endpoint works: `POST /api/v4/deep-research`
- [ ] Job status endpoint works: `GET /api/v4/job/{id}`
- [ ] Jobs persist across restarts ✅

### Monitoring
- [ ] Set up Redis metrics monitoring in Railway
- [ ] Check memory usage (should be < 25 MB on free tier)
- [ ] Monitor job creation/completion rates
- [ ] Track average job processing time

### Optional: Test Cleanup Endpoint
```bash
curl -X DELETE https://your-app.railway.app/api/v4/admin/cleanup-jobs
```

Expected response:
```json
{
  "message": "Job cleanup is automatic (24-hour TTL)",
  "redis_connected": true,
  "cleanup_method": "Redis setex auto-expiration"
}
```

## Success Criteria

✅ **Deployment successful if:**
1. Redis connects on startup (check logs)
2. Jobs can be created and retrieved
3. Jobs persist after server restart
4. Progress updates work correctly
5. Completed jobs include full reports
6. Jobs auto-expire after 24 hours

## Rollback Plan

If Redis causes issues:

1. **Revert to previous version:**
   ```bash
   git revert HEAD
   git push
   ```

2. **Or disable Redis temporarily:**
   - Remove `REDIS_URL` from Railway environment variables
   - Code will automatically fall back to in-memory storage
   - Jobs will work but not persist across restarts

3. **Debug locally:**
   ```bash
   # Start local Redis
   brew services start redis  # Mac
   # or
   docker run -d -p 6379:6379 redis:7-alpine

   # Run test suite
   python3 test_redis_jobs.py

   # Run backend locally
   python3 main.py
   ```

## Next Steps After Deployment

1. Monitor Redis metrics for 24 hours
2. Check job success/failure rates
3. Verify no memory leaks in Redis
4. Consider upgrading to Redis Pro if hitting limits
5. Implement job analytics dashboard (optional)
6. Add webhook notifications for job completion (optional)

## Notes

- **TTL**: Jobs auto-expire after 24 hours
- **Fallback**: In-memory storage if Redis unavailable
- **Storage**: Railway Free = 25 MB, Pro = Unlimited
- **Connections**: Redis handles concurrent access automatically
- **Security**: Railway manages Redis authentication

---

## Support Commands

```bash
# Check if Redis is running locally
redis-cli ping

# Connect to local Redis
redis-cli

# List all jobs in Redis
redis-cli KEYS "job:*"

# Get specific job
redis-cli GET "job:{job_id}"

# Check TTL of a job
redis-cli TTL "job:{job_id}"

# Clear all jobs (DANGER!)
redis-cli FLUSHDB
```

---

**Deployment Date:** _____________

**Deployed By:** _____________

**Redis Version:** 7.x

**Backend Version:** v4.0 (with Redis persistence)

**Status:** ⬜ Pending | ⬜ In Progress | ⬜ Complete | ⬜ Issues
