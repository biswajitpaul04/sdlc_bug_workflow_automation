# 🎯 On-Click Workflow Setup Guide (No Cron Needed!)

This is a **much simpler** approach than GitHub Actions:
- ✅ No complicated cron schedules
- ✅ No GitHub needed
- ✅ Manual control - click button to run
- ✅ Works on your local machine
- ✅ Real-time dashboard

---

## 🎨 Architecture

```
Your Computer
┌─────────────────────────────────────┐
│  Dashboard (browser)                │
│  ┌─────────────────────────────────┐│
│  │ Click "Run Workflow" button      ││
│  └──────────────┬────────────────────┘│
│                 │ HTTP request        │
│                 ↓                     │
│  ┌─────────────────────────────────┐│
│  │ API Server (api_server.py)      ││
│  │ Listens on localhost:5000       ││
│  └──────────────┬────────────────────┘│
│                 │                     │
│                 ↓                     │
│  ┌─────────────────────────────────┐│
│  │ Workflow (bug_workflow.py)       ││
│  │ Checks Jira, generates code     ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## 📋 Setup Steps (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

You'll need:
- `requests` - for API calls
- `python-dotenv` - for .env file
- `flask` - for API server ← NEW
- `flask-cors` - for cross-origin requests ← NEW

### Step 2: Create .env File

Same as before - add your 5 API keys:

```bash
JIRA_API_URL=https://biswajitpaulckp2010.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=atk_xxxxxxxxxxxx
JIRA_PROJECT_KEY=SCRUM
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx
```

### Step 3: Start the API Server

**Terminal/Command Prompt:**

```bash
python api_server.py
```

**You should see:**
```
🚀 Bug Workflow API Server Starting...
📍 Server: http://localhost:5000
📊 Dashboard: http://localhost:5000/dashboard.html
📋 API Docs:
   GET  /api/status    - Get workflow status
   POST /api/trigger   - Trigger workflow
   GET  /api/logs      - Get execution logs
   GET  /api/health    - Health check
   GET  /api/config    - Get configuration

⏸️  Press Ctrl+C to stop
```

✅ **API Server is Running!**

### Step 4: Open Dashboard

**In your browser, open:**
```
http://localhost:5000
```

Or directly:
```
http://localhost:5000/dashboard_interactive.html
```

You should see:
- 🟢 Green "Connected" status
- Blue "Run workflow now" button
- Empty log viewer
- Configuration loaded

### Step 5: Click the Button!

1. Click **"Run workflow now"** button
2. Watch the steps animate
3. See logs in real-time
4. Check your Jira - bugs should be marked "In Progress"!

---

## 📊 What Happens When You Click

```
You click "Run workflow now"
         ↓
Dashboard sends POST request to API
         ↓
API Server receives request
         ↓
Starts Python workflow in background
         ↓
Workflow runs:
  1. Connects to Jira
  2. Finds new bugs
  3. Marks as "In Progress"
  4. Generates code with Claude
  5. Saves solutions
         ↓
API returns success
         ↓
Dashboard updates with results
         ↓
You see logs and status
```

---

## 🎮 Dashboard Features

### Status Display
- Shows workflow status (Idle, Running, Completed, Error)
- Last run timestamp
- Bugs processed count
- API connection status

### Controls
- ▶ **Run workflow now** - Click to trigger
- 🔄 **Refresh status** - Manual refresh
- 📖 **API documentation** - See available endpoints

### Monitoring
- 5-step workflow visualization
- Real-time execution logs
- Auto-refresh every 5 seconds
- Configuration display

### Alerts
- Success messages (green)
- Error messages (red)
- Info messages (blue)

---

## 🔧 Configuration

### Change API Server Port

**Edit `api_server.py`:**
```python
app.run(
    host='0.0.0.0',
    port=5001,  # Change this
    debug=True,
    use_reloader=False
)
```

Then update dashboard URL:
```
http://localhost:5001
```

### Access from Other Computers

**Edit `api_server.py`:**
```python
app.run(
    host='0.0.0.0',  # Listen on all network interfaces
    port=5000,
    debug=True,
    use_reloader=False
)
```

Then access from another computer:
```
http://YOUR_COMPUTER_IP:5000
```

Find your IP:
- **Windows:** `ipconfig` → look for IPv4 address
- **Mac/Linux:** `ifconfig` → look for inet address

---

## 📡 API Endpoints

### GET `/api/status`
Get current workflow status

**Response:**
```json
{
  "status": "idle",
  "last_run": "2024-01-15T14:32:45.123456",
  "bugs_processed": 2,
  "error": null
}
```

### POST `/api/trigger`
Trigger the workflow manually

**Response:**
```json
{
  "status": "success",
  "message": "Workflow triggered",
  "timestamp": "2024-01-15T14:33:00.123456"
}
```

### GET `/api/logs`
Get recent execution logs

**Response:**
```json
{
  "logs": [
    "[14:32:05] Starting workflow...",
    "[14:32:09] Found 2 bugs",
    "[14:32:45] Code generated"
  ]
}
```

### GET `/api/health`
Health check

**Response:**
```json
{
  "status": "ok",
  "api_version": "1.0",
  "timestamp": "2024-01-15T14:33:00.123456"
}
```

### GET `/api/config`
Get configuration (non-sensitive)

**Response:**
```json
{
  "jira_url": "https://biswajitpaulckp2010.atlassian.net",
  "jira_project": "SCRUM",
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

---

## 🧪 Test Locally

### Step 1: Make sure API is running
```bash
python api_server.py
```

### Step 2: Test health check
```bash
curl http://localhost:5000/api/health
```

You should see:
```json
{"status":"ok","api_version":"1.0","timestamp":"..."}
```

### Step 3: Test trigger (from another terminal)
```bash
curl -X POST http://localhost:5000/api/trigger
```

You should see:
```json
{"status":"success","message":"Workflow triggered","timestamp":"..."}
```

### Step 4: Check status
```bash
curl http://localhost:5000/api/status
```

---

## 🚀 Deployment Options

### Option A: Local Only (Development)
```bash
python api_server.py
```
- ✅ Simple
- ✅ Works on your computer
- ❌ Only accessible locally
- ❌ Requires computer to stay on

### Option B: Docker (Self-Hosted)

**Create `Dockerfile`:**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "api_server.py"]
```

**Create `docker-compose.yml`:**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - JIRA_API_URL=${JIRA_API_URL}
      - JIRA_EMAIL=${JIRA_EMAIL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - JIRA_PROJECT_KEY=${JIRA_PROJECT_KEY}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
    volumes:
      - ./solutions:/app/solutions
```

**Run:**
```bash
docker-compose up -d
```

Access at: `http://localhost:5000`

### Option C: Cloud (Heroku, Replit, etc.)

Would need additional setup. Contact if interested!

---

## 🐛 Troubleshooting

### "Connection refused at localhost:5000"
- ✓ Make sure API server is running: `python api_server.py`
- ✓ Check no other app is using port 5000
- ✓ Try different port (see Configuration section)

### "404 Not Found when opening dashboard"
- ✓ Use full URL: `http://localhost:5000/dashboard_interactive.html`
- ✓ Make sure files are in same directory as api_server.py

### "Workflow fails with 'Cannot authenticate to Jira'"
- ✓ Check .env file has correct credentials
- ✓ Verify Jira API token is valid
- ✓ Check email matches Jira account

### "Claude API errors"
- ✓ Verify Claude API key is correct
- ✓ Check you have free credits or paid plan
- ✓ Verify API key format (starts with `sk-ant-`)

### Dashboard shows "Disconnected"
- ✓ API server not running - run `python api_server.py`
- ✓ Wrong URL in dashboard - check browser address bar
- ✓ Port mismatch - make sure using port 5000 (or your custom port)

---

## 📁 File Structure

```
your-project/
├── api_server.py              ← NEW! Start this
├── dashboard_interactive.html  ← NEW! Open this in browser
├── bug_workflow.py            ← Existing
├── requirements.txt           ← Updated (added Flask)
├── .env                       ← Your credentials
├── .gitignore                 ← Hide .env
└── solutions/                 ← Generated code (auto-created)
```

---

## ✅ Complete Checklist

- [ ] `requirements.txt` updated
- [ ] Flask installed: `pip install -r requirements.txt`
- [ ] `.env` file created with 5 values
- [ ] API server running: `python api_server.py`
- [ ] Dashboard accessible: `http://localhost:5000`
- [ ] API shows "Connected" status
- [ ] Click "Run workflow now" works
- [ ] Check Jira - bugs marked "In Progress"
- [ ] Check solutions folder - code generated

---

## 🎯 Advantages Over Cron/GitHub Actions

| Feature | On-Click (You) | Cron | GitHub Actions |
|---------|---|---|---|
| **Ease of setup** | ✅ Simple (2 commands) | ❌ Complex cron syntax | ❌ Multiple steps |
| **Manual control** | ✅ Click button | ❌ No control | ❌ Limited control |
| **Real-time feedback** | ✅ Live dashboard | ❌ Check logs later | ❌ Check logs later |
| **Dashboard** | ✅ Beautiful UI | ❌ CLI only | ❌ GitHub only |
| **No schedule needed** | ✅ Run when you want | ❌ Fixed schedule | ❌ Fixed schedule |
| **Works locally** | ✅ Yes | ✅ Yes | ❌ Cloud only |
| **Automatic runs** | ❌ No | ✅ Yes | ✅ Yes |

---

## 🎉 You're Ready!

```bash
# 1. Start API server
python api_server.py

# 2. Open dashboard in browser
http://localhost:5000

# 3. Click "Run workflow now"

# 4. Watch it work! 🚀
```

---

## 💡 Next Steps

**Want to automate it later?**
- Can add scheduler using APScheduler
- Can set up cron job to call `/api/trigger`
- Can integrate with GitHub Actions

**For now, manual control is perfect!**

---

**Questions? Check the logs in the dashboard for detailed error messages!**
