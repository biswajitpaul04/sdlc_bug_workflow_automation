# Bug Automation Workflow - Complete Deployment Guide

## Project Overview

This is a complete automated system that:
1. **Runs on schedule** - Every hour (configurable)
2. **Checks Jira** - Finds newly created bugs
3. **Updates status** - Marks bugs as "In Progress"
4. **Generates solutions** - Uses Claude API to create code fixes
5. **Monitors progress** - Dashboard to track all activities

---

## Project Structure

```
bug-automation-workflow/
├── bug-workflow.js           # Node.js implementation
├── bug-workflow.py           # Python implementation
├── bug_workflow_implementation.md  # Detailed implementation docs
├── dashboard.html            # Standalone web dashboard
├── package.json              # Node.js dependencies
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Local environment (DO NOT COMMIT)
├── .github/workflows/
│   └── bug-checker.yml       # GitHub Actions automation
├── solutions/                # Generated code solutions (auto-created)
├── logs/                     # Workflow logs (auto-created)
└── README.md                 # This file

```

---

## Quick Start (5 minutes)

### Step 1: Get API Keys

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token (save it securely)

**Claude API Key:**
1. Go to https://console.anthropic.com/
2. Click "API keys" in the left sidebar
3. Click "Create key"
4. Copy the key (save it securely)

### Step 2: Clone and Setup

```bash
git clone https://github.com/yourusername/bug-automation-workflow.git
cd bug-automation-workflow

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Step 3: Configure Environment

**File: `.env`**
```bash
# Jira Configuration
JIRA_API_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your-jira-api-token-here
JIRA_PROJECT_KEY=PROJ

# Claude API
CLAUDE_API_KEY=sk-ant-...

# Optional
LOG_LEVEL=info
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

### Step 4: Install Dependencies

**For Node.js:**
```bash
npm install
node bug-workflow.js
```

**For Python:**
```bash
pip install -r requirements.txt
python bug_workflow.py
```

### Step 5: View Dashboard

1. Open `dashboard.html` in your browser
2. Or serve it with a web server:
   ```bash
   python -m http.server 8000
   # Visit http://localhost:8000/dashboard.html
   ```

---

## Deployment Options

### Option 1: GitHub Actions (Cloud - Easiest)

**Setup:**

1. Push this repo to GitHub
2. Create GitHub Secrets:
   - Go to Settings → Secrets and variables → Actions
   - Add secrets: `JIRA_API_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`, `CLAUDE_API_KEY`

3. The workflow runs automatically every hour via `.github/workflows/bug-checker.yml`

**Advantages:**
- No server to maintain
- Free for public repos
- GitHub integrations
- Easy to monitor

**Cost:** Free (included with GitHub)

---

### Option 2: Docker + Docker Compose

**Create: `Dockerfile`**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY bug-workflow.js .
COPY .env .

CMD ["node", "bug-workflow.js"]
```

**Create: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  bug-workflow:
    build: .
    restart: always
    environment:
      - JIRA_API_URL=${JIRA_API_URL}
      - JIRA_EMAIL=${JIRA_EMAIL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - JIRA_PROJECT_KEY=${JIRA_PROJECT_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    volumes:
      - ./solutions:/app/solutions
      - ./logs:/app/logs

  dashboard:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./dashboard.html:/usr/share/nginx/html/index.html:ro
    depends_on:
      - bug-workflow
```

**Run:**
```bash
docker-compose up -d
# Access dashboard at http://localhost:8080
```

---

### Option 3: AWS Lambda + CloudWatch

**Create: `lambda_handler.py`**
```python
import json
from bug_workflow import main

def lambda_handler(event, context):
    try:
        result = main()
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**Setup CloudWatch Events:**
1. AWS Console → CloudWatch → Events → Rules
2. Create rule with schedule: `rate(1 hour)`
3. Target: Lambda function → `lambda_handler`
4. Set environment variables in Lambda configuration

**Cost:** First 1 million requests free, then ~$0.20 per million

---

### Option 4: Google Cloud Functions

**Create: `main.py`**
```python
from bug_workflow import main

def run_workflow(request):
    result = main()
    return result

if __name__ == '__main__':
    run_workflow(None)
```

**Deploy:**
```bash
gcloud functions deploy run_workflow \
  --runtime python39 \
  --trigger-topic bug-workflow \
  --entry-point run_workflow
```

**Schedule with Cloud Scheduler:**
```bash
gcloud scheduler jobs create pubsub bug-workflow-hourly \
  --schedule="0 * * * *" \
  --topic=bug-workflow
```

**Cost:** 2 million free invocations/month, then ~$0.40 per million

---

### Option 5: Self-Hosted (Cron Job)

**Setup on Linux/Mac:**

```bash
# Make script executable
chmod +x setup-cron.sh
./setup-cron.sh

# Verify
crontab -l
```

**Manual cron setup:**
```bash
crontab -e

# Add this line:
0 * * * * cd /path/to/bug-workflow && /usr/bin/node bug-workflow.js >> /var/log/bug-workflow.log 2>&1
```

**Cost:** Only your server costs

---

## HTML Dashboard Deployment

### Standalone (No Backend)

Simply open `dashboard.html` in any browser. The dashboard works with sample data and shows:
- ✓ Workflow status
- ✓ Active bugs
- ✓ Execution logs
- ✓ Configuration panel
- ✓ Recent solutions

**Limitations:** Data is simulated. To connect to real data, you need a backend API.

### With Backend API

Create a REST API backend to serve real data:

**Create: `api.js` (Express.js example)**
```javascript
const express = require('express');
const cors = require('cors');
const { main } = require('./bug-workflow');

const app = express();
app.use(cors());

app.get('/api/metrics', (req, res) => {
  res.json({
    bugsProcessed: 24,
    successRate: 92,
    avgGenerationTime: 34,
    nextRunIn: 45
  });
});

app.get('/api/bugs', (req, res) => {
  // Fetch from database or cache
  res.json([
    {
      key: 'BUG-1247',
      title: 'Login page crashes on Safari',
      priority: 'High',
      status: 'In Progress'
    }
  ]);
});

app.post('/api/workflow/run', async (req, res) => {
  const result = await main();
  res.json(result);
});

app.listen(3000, () => {
  console.log('API running on port 3000');
});
```

**Update dashboard.html to use API:**
```javascript
// In dashboard.html, replace simulated data:
fetch('/api/metrics')
  .then(r => r.json())
  .then(data => {
    document.getElementById('metricsValue').textContent = data.bugsProcessed;
  });
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `JIRA_API_URL` | Yes | - | `https://company.atlassian.net` |
| `JIRA_EMAIL` | Yes | - | `user@company.com` |
| `JIRA_API_TOKEN` | Yes | - | `atk_xxxxx` |
| `JIRA_PROJECT_KEY` | Yes | - | `PROJ` |
| `CLAUDE_API_KEY` | Yes | - | `sk-ant-xxxxx` |
| `LOG_LEVEL` | No | `info` | `debug`, `info`, `warn`, `error` |
| `SLACK_WEBHOOK` | No | - | `https://hooks.slack.com/...` |
| `MAX_BUGS_PER_RUN` | No | 50 | Any number |
| `CLAUDE_MODEL` | No | `claude-opus-4-1` | `claude-sonnet-4-20250514`, `claude-haiku-3-5` |

### Cron Schedule Examples

| Schedule | Frequency |
|----------|-----------|
| `0 * * * *` | Every hour |
| `0 */2 * * *` | Every 2 hours |
| `0 0,12 * * *` | Twice daily (midnight, noon) |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * MON-FRI` | Business hours, weekdays only |
| `*/15 * * * *` | Every 15 minutes |

---

## Monitoring & Logging

### Log Files

- **Standard output:** `stdout` (captured by your deployment platform)
- **Error logs:** Check your platform's error tracking
- **Solution files:** Stored in `solutions/` directory

### Log Levels

```javascript
logger.log('Info message');      // INFO
logger.error('Error message');   // ERROR
```

### Slack Notifications (Optional)

Set `SLACK_WEBHOOK` environment variable to get notifications:

```bash
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### CloudWatch / Datadog Integration

**Example: CloudWatch**
```javascript
const CloudWatch = require('aws-sdk/clients/cloudwatch');

const cloudwatch = new CloudWatch();
cloudwatch.putMetricData({
  Namespace: 'BugWorkflow',
  MetricData: [{
    MetricName: 'BugsProcessed',
    Value: processedCount,
    Unit: 'Count'
  }]
}).promise();
```

---

## Troubleshooting

### "Jira API authentication failed"
- ✓ Verify API token is correct
- ✓ Check email address matches Jira account
- ✓ Ensure token hasn't expired (regenerate if needed)

### "No bugs found, but there are open bugs"
- ✓ Check `JIRA_PROJECT_KEY` matches your project
- ✓ Verify JQL query in `getNewBugsFromJira()` function
- ✓ Check bug is in "Open" status (not closed)

### "Claude API rate limit exceeded"
- ✓ Reduce bugs processed per run: `MAX_BUGS_PER_RUN=10`
- ✓ Use cheaper model: `CLAUDE_MODEL=claude-haiku-3-5`
- ✓ Add delays between requests

### Dashboard not updating
- ✓ Open browser dev tools (F12)
- ✓ Check Console tab for errors
- ✓ Verify API endpoint is accessible
- ✓ Check CORS headers if using API

### Workflow not running
- ✓ Check cron job is installed: `crontab -l`
- ✓ Check GitHub Actions is enabled (if using)
- ✓ Verify environment variables are set
- ✓ Check logs for errors

---

## Security Best Practices

1. **Never commit `.env` file** - Always use `.env.example` as template
2. **Use GitHub Secrets** - Store tokens in platform-specific secret management
3. **Rotate API tokens** - Regularly regenerate Jira and Claude tokens
4. **Limit permissions** - Create Jira user with only necessary permissions
5. **Audit logs** - Monitor who accessed the workflow and when
6. **HTTPS only** - Always use HTTPS for API calls
7. **Rate limiting** - Set reasonable limits to prevent abuse

---

## Performance Optimization

### Cost Reduction

1. **Use Claude Haiku** for simple bugs:
   ```bash
   CLAUDE_MODEL=claude-haiku-3-5
   ```
   Saves ~95% on API costs

2. **Reduce frequency** if hourly is overkill:
   ```bash
   # Run 4 times daily instead of hourly
   0 0,6,12,18 * * *
   ```

3. **Batch processing** - Process multiple bugs per API call

### Speed Improvement

1. **Parallel processing** - Process bugs concurrently (careful with rate limits)
2. **Caching** - Cache frequently accessed bug data
3. **Async operations** - Use non-blocking I/O

---

## Scaling

### For High Volume (1000+ bugs/day)

1. **Distributed workers** - Run multiple instances in parallel
2. **Message queue** - Use Redis/RabbitMQ to queue bugs
3. **Database** - Store results in PostgreSQL/MongoDB instead of files
4. **Load balancing** - Distribute requests across servers

**Recommended architecture:**
```
Jira → Message Queue → Worker Processes → Database → API → Dashboard
```

---

## API Reference (Backend)

### GET `/api/metrics`
Returns workflow metrics
```json
{
  "bugsProcessed": 24,
  "successRate": 92,
  "avgGenerationTime": 34,
  "nextRunIn": 45
}
```

### GET `/api/bugs`
List all active bugs
```json
[
  {
    "key": "BUG-1247",
    "title": "Login page crashes",
    "status": "In Progress",
    "priority": "High"
  }
]
```

### POST `/api/workflow/run`
Manually trigger workflow
```json
{
  "status": "completed",
  "bugsProcessed": 2,
  "duration": "1m 45s"
}
```

### GET `/api/solutions/{bugKey}`
Get generated solution for a bug
```json
{
  "bugKey": "BUG-1247",
  "solution": "# Root Cause...",
  "generatedAt": "2024-01-15T14:32:45Z"
}
```

---

## Support & Resources

- **Jira API**: https://developer.atlassian.com/cloud/jira/rest/v3/
- **Claude API**: https://docs.anthropic.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Docker**: https://docs.docker.com/
- **Cron**: https://crontab.guru/

---

## License

MIT License - Feel free to use and modify

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Last updated:** January 2024
**Version:** 1.0.0
