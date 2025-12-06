# 🚀 Quick Start: Redis Job Persistence

## TL;DR - What Changed?

Deep Research jobs now persist in Redis instead of memory, so they survive server restarts on Railway.

---

## 📦 Installation (Local Development)

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## ✅ Test It Works

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 test_redis_jobs.py
```

**Expected:**
```
✅ Redis connected: redis://localhost:6379
✅ Job saved to Redis: test-123
✅ Job retrieved from Redis
✅ ALL TESTS PASSED
```

---

## 🚢 Deploy to Railway

### 1. Add Redis Database
1. Go to Railway dashboard
2. Click **"+ New"** → **"Database"** → **"Add Redis"**
3. Wait 1-2 minutes for provisioning

### 2. Deploy Code
```bash
git add .
git commit -m "Add Redis job persistence"
git push
```

### 3. Verify in Logs
Look for:
```
✅ Redis connected: redis://default:***@redis.railway.internal:6379
```

---

## 🧪 Test Persistence

### Create Job
```bash
curl -X POST https://your-app.railway.app/api/v4/deep-research \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Test Product",
    "brand": "Test",
    "category": "food",
    "ingredients": ["Water"]
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### Check Status
```bash
curl https://your-app.railway.app/api/v4/job/550e8400-e29b-41d4-a716-446655440000
```

### Restart Server
1. Go to Railway dashboard
2. Click **"Deploy"** → **"Restart"**
3. Check job status again - **it should still be there!** ✅

---

## 🛠️ Troubleshooting

### ❌ "Redis connection failed"

**Fix:**
1. Check Redis add-on exists in Railway
2. Verify `REDIS_URL` environment variable
3. Restart backend service

### ❌ "Job not found" after restart

**Fix:**
1. Check logs for Redis connection status
2. Ensure Redis is running
3. Verify `REDIS_URL` is set correctly

---

## 📚 Documentation

- **Full Setup Guide:** `REDIS_SETUP.md`
- **Deployment Checklist:** `DEPLOYMENT_CHECKLIST.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`

---

## 🎯 Key Features

✅ Jobs persist across restarts
✅ Automatic 24-hour cleanup
✅ Graceful fallback to in-memory
✅ Zero API changes
✅ Production-ready

---

## 📞 Support

**Redis not working?**
```bash
# Check if Redis is running
redis-cli ping

# View all jobs
redis-cli KEYS "job:*"

# Get specific job
redis-cli GET "job:550e8400-..."
```

**Still having issues?**
- Check `REDIS_SETUP.md` for detailed troubleshooting
- Run `python3 test_redis_jobs.py` to diagnose
- Verify Railway Redis service is running

---

**Need more details?** See `REDIS_SETUP.md` or `IMPLEMENTATION_SUMMARY.md`
