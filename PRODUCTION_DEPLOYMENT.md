# Production Deployment Guide

## Scheduler Overview

The video scheduler runs automatically to:
- Generate videos 6 hours before scheduled upload time
- Respect monthly video limits (12/30/60 for Launch/Grow/Scale)
- **Distribute videos across ALL user's series** (not per-series)
- Upload at user-selected times

---

## Important: Video Frequency for Multiple Series

### How Limits Work

**Monthly limits MULTIPLY by number of series purchased:**

| Plan   | Base Frequency | 1 Series | 2 Series | 3 Series |
|--------|----------------|----------|----------|----------|
| Launch | 3x/week each   | 12/mo    | 24/mo    | 36/mo    |
| Grow   | Daily each     | 30/mo    | 60/mo    | 90/mo    |
| Scale  | 2x/day each    | 60/mo    | 120/mo   | 180/mo   |

**Each series generates videos independently at its own frequency.**

### Example Scenario

**User has Grow plan and 2 series:**
- Monthly limit: 30 × 2 = **60 videos TOTAL**
- Series A: Generates 1 video daily = ~30 videos/month
- Series B: Generates 1 video daily = ~30 videos/month
- **Total: ~60 videos/month**

**User has Scale plan and 2 series:**
- Monthly limit: 60 × 2 = **120 videos TOTAL**
- Series A: Generates 2 videos daily = ~60 videos/month
- Series B: Generates 2 videos daily = ~60 videos/month
- **Total: ~120 videos/month**

---

## Deployment Options

### 1. Windows Task Scheduler ✅ (Recommended for Windows)

**Setup:**
```bash
# Run as Administrator
python setup_scheduler.py
```

**If you get "schtasks not recognized":**
1. Open PowerShell or CMD **as Administrator**
2. Re-run: `python setup_scheduler.py`

**Or manually import:**
1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Click "Import Task..."
3. Select `scheduler_task.xml`
4. Click OK

**Verify:**
```bash
schtasks /Query /TN "YouTubeAutomationScheduler"
```

**Production notes:**
- ✅ Starts automatically on boot
- ✅ Runs in background
- ✅ Survives reboots
- ✅ No dependencies needed

---

### 2. Linux Systemd Service (Recommended for Linux)

**Files already created:**
- `youtube-automation-scheduler.service`
- `youtube-automation-scheduler.timer`

**Install:**
```bash
sudo cp youtube-automation-scheduler.service /etc/systemd/system/
sudo cp youtube-automation-scheduler.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable youtube-automation-scheduler.timer
sudo systemctl start youtube-automation-scheduler.timer
```

**Verify:**
```bash
sudo systemctl status youtube-automation-scheduler.timer
sudo journalctl -u youtube-automation-scheduler.service -f
```

**Production notes:**
- ✅ Runs as system service
- ✅ Auto-starts on boot
- ✅ Reliable and battle-tested

---

### 3. AWS Deployment

**Option A: EventBridge + Lambda**
1. Package your app: `zip -r app.zip . -x "*.git*" "*.venv*"`
2. Create Lambda function (Python 3.11)
3. Upload app.zip
4. Create EventBridge rule: `rate(1 hour)`
5. Set handler: `scheduler.lambda_handler`

**Add to scheduler.py:**
```python
def lambda_handler(event, context):
    """AWS Lambda handler"""
    import asyncio
    asyncio.run(run_scheduler_once())
    return {"statusCode": 200, "body": "OK"}
```

**Option B: EC2 + Cron**
```bash
# SSH to EC2 instance
crontab -e

# Add line:
0 * * * * cd /path/to/app && /path/to/venv/bin/python scheduler.py --mode once
```

---

### 4. Google Cloud Platform

**Cloud Scheduler + Cloud Functions:**

1. Deploy function:
```bash
gcloud functions deploy video-scheduler \
  --runtime python311 \
  --trigger-http \
  --entry-point run_scheduler \
  --memory 2GB
```

2. Create Cloud Scheduler job:
```bash
gcloud scheduler jobs create http video-scheduler-job \
  --schedule="0 * * * *" \
  --uri="https://YOUR-REGION-YOUR-PROJECT.cloudfunctions.net/video-scheduler"
```

---

### 5. Azure Deployment

**Azure Functions + Timer Trigger:**

1. Create `function.json`:
```json
{
  "bindings": [{
    "name": "timer",
    "type": "timerTrigger",
    "direction": "in",
    "schedule": "0 0 * * * *"
  }]
}
```

2. Deploy:
```bash
func azure functionapp publish YOUR-APP-NAME
```

---

### 6. Heroku

**Heroku Scheduler Add-on:**

1. Add scheduler:
```bash
heroku addons:create scheduler:standard
```

2. Configure job:
```bash
heroku addons:open scheduler
# Add job: python scheduler.py --mode once
# Frequency: Every hour
```

**Or use Procfile (worker dyno):**
```
worker: python scheduler.py --mode service
```

Then:
```bash
heroku ps:scale worker=1
```

---

### 7. Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run scheduler as service
CMD ["python", "scheduler.py", "--mode", "service"]
```

**Build and run:**
```bash
docker build -t youtube-automation .
docker run -d --name scheduler \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  youtube-automation
```

**With Docker Compose:**
```yaml
version: '3.8'
services:
  scheduler:
    build: .
    container_name: youtube-scheduler
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./output:/app/output
    environment:
      - DATABASE_URL=postgresql://...
```

Run:
```bash
docker-compose up -d
```

---

### 8. Python Service (Any Platform)

**Using APScheduler:**

```bash
pip install apscheduler
```

Then run:
```bash
# Run as continuous service
python scheduler.py --mode service
```

**Keep it running with Supervisor (Linux):**

Create `/etc/supervisor/conf.d/youtube-scheduler.conf`:
```ini
[program:youtube-scheduler]
command=/path/to/venv/bin/python /path/to/app/scheduler.py --mode service
directory=/path/to/app
user=yourusername
autostart=true
autorestart=true
stderr_logfile=/var/log/youtube-scheduler.err.log
stdout_logfile=/var/log/youtube-scheduler.out.log
```

Start:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start youtube-scheduler
```

---

## Monitoring & Logs

### View Logs

**Local:**
```bash
# Real-time
tail -f logs/scheduler.log

# Windows
type logs\scheduler.log
```

**Systemd (Linux):**
```bash
sudo journalctl -u youtube-automation-scheduler.service -f
```

**Docker:**
```bash
docker logs -f scheduler
```

### Log Rotation

**Linux (logrotate):**

Create `/etc/logrotate.d/youtube-scheduler`:
```
/path/to/app/logs/scheduler.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 user user
}
```

---

## Troubleshooting

### Scheduler not running?

**Windows:**
```bash
schtasks /Query /TN "YouTubeAutomationScheduler"
schtasks /Run /TN "YouTubeAutomationScheduler"  # Manual run
```

**Linux:**
```bash
sudo systemctl status youtube-automation-scheduler.timer
sudo systemctl restart youtube-automation-scheduler.timer
```

### Videos not generating?

Check logs for:
- Monthly limit reached
- Series limit exceeded  
- User has multiple series but limit distributed
- Not within generation window

### Test manually

```bash
python scheduler.py --mode once
```

---

## Production Checklist

- [ ] Environment variables configured (API keys, database)
- [ ] Logs directory exists and writable
- [ ] Database migrations run
- [ ] Scheduler task/service created
- [ ] Verified scheduler runs (check logs)
- [ ] Tested with real series
- [ ] Monitoring set up (logs, alerts)
- [ ] Backup strategy for videos/database

---

## Best Practices

1. **Start Small**: Test with 1-2 users first
2. **Monitor Logs**: Check logs daily for first week
3. **Set Alerts**: Alert on errors or failed generations
4. **Resource Planning**: Ensure enough disk space for videos
5. **Database Backups**: Backup DB before/after generations
6. **Rate Limiting**: YouTube/TikTok API rate limits respected
7. **Retry Logic**: Failed generations are logged (add retry if needed)

---

## Summary

**For Production:**

| Platform | Best Option |
|----------|-------------|
| Windows Server | Task Scheduler ✅ |
| Linux Server | Systemd Service ✅ |
| AWS | EventBridge + Lambda |
| Google Cloud | Cloud Scheduler + Functions |
| Azure | Azure Functions |
| Heroku | Worker Dyno |
| Docker | Container with restart policy |
| Any | Python Service + Supervisor |

**Recommended: Windows Task Scheduler or Linux Systemd** - Most reliable, no additional dependencies.
