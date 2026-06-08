# Bug Automation Workflow - Quick Start Guide

## 📦 What You've Received

You now have a **complete automated bug checking and code generation system** with:

1. ✅ **Workflow Scripts** - Node.js and Python implementations
2. ✅ **HTML Dashboard** - Interactive web interface with real-time monitoring
3. ✅ **API Integration** - Jira API + Claude API
4. ✅ **Scheduling Options** - GitHub Actions, Docker, AWS Lambda, Cloud Functions, Cron
5. ✅ **Documentation** - Complete deployment and troubleshooting guides

---

## 🚀 Deploy in 5 Minutes

### Step 1: Get Your API Keys (2 min)

**Jira API Token:**
- Go to: https://id.atlassian.com/manage-profile/security/api-tokens
- Click "Create API token"
- Copy the token (you'll need this)

**Claude API Key:**
- Go to: https://console.anthropic.com/api-keys
- Click "Create key"
- Copy the key (you'll need this)

### Step 2: Set Up Environment (2 min)

```bash
# Create .env file with your credentials
cat > .env << EOF
JIRA_API_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your-jira-api-token-here
JIRA_PROJECT_KEY=PROJ
CLAUDE_API_KEY=sk-ant-xxxxx
EOF
```

### Step 3: Choose Your Deployment (1 min)

**Option A: GitHub Actions (Easiest - Cloud)**
```bash
# Push to GitHub
git add .
git commit -m "Initial commit"
git push origin main

# Go to GitHub Settings → Secrets and add:
# - JIRA_API_URL
# - JIRA_EMAIL
# - JIRA_API_TOKEN
# - JIRA_PROJECT_KEY
# - CLAUDE_API_KEY

# Workflow runs automatically every hour!
```

**Option B: Docker (Best - Self-hosted)**
```bash
docker-compose up -d
# Dashboard at http://localhost:8080
# Runs automatically in background
```

**Option C: Local Cron Job (Simple)**
```bash
chmod +x setup-cron.sh
./setup-cron.sh
# Runs automatically every hour
```

**Option D: Node.js (Development)**
```bash
npm install
npm start
# Runs once and exits (good for testing)
```

**Option E: Python (Development)**
```bash
pip install -r requirements.txt
python bug_workflow.py
# Runs once and exits (good for testing)
```

---

## 📊 Using the Dashboard

Open **`dashboard.html`** in your browser to:

- 📈 View metrics (bugs processed, success rate, etc.)
- 🔄 Monitor workflow status in real-time
- 🐛 See active bugs being processed
- 📋 View execution logs
- ⚙️ Configure settings
- 💾 Review generated solutions

**Run Workflow Manually:**
Click "Run workflow now" button to trigger immediately

---

## 📁 File Structure

```
your-project/
├── bug_workflow_implementation.md  ← Detailed implementation docs
├── bug_workflow.py                 ← Python workflow (production-ready)
├── package.json                    ← Node.js dependencies
├── dashboard.html                  ← Web interface (just open in browser)
├── DEPLOYMENT_GUIDE.md             ← Complete deployment instructions
├── requirements.txt                ← Python dependencies
├── .env                            ← Your credentials (keep secret!)
└── .env.example                    ← Template for .env
```

---

## 🎯 How It Works (Simplified)

```
Every Hour
    ↓
Check Jira API for new bugs
    ↓
Found bugs?
    ├→ YES: For each bug...
    │   ├→ Mark as "In Progress"
    │   ├→ Send to Claude API
    │   ├→ Get code solution back
    │   ├→ Save to solutions/ folder
    │   └→ Log the result
    └→ NO: Wait for next hour
```

---

## 🔑 Key Configuration

**Change the schedule:**
```bash
# Edit JIRA_PROJECT_KEY to match your project
JIRA_PROJECT_KEY=MYPROJ

# Change Claude model (balance speed vs quality)
# claude-opus-4-1 (best quality, slower)
# claude-sonnet-4-20250514 (balanced, recommended)
# claude-haiku-3-5 (fastest, cheapest)
```

**Adjust Jira query:**
- Edit `getNewBugsFromJira()` function in workflow file
- Change filter criteria (priority, labels, assignee, etc.)

**Change schedule frequency:**
```bash
# Every hour (default)
0 * * * *

# Every 30 minutes
*/30 * * * *

# Twice daily
0 0,12 * * *

# Business hours weekdays
0 9-17 * * MON-FRI
```

---

## 🧪 Test It

**Before deploying to production:**

1. **Test Node.js version:**
   ```bash
   npm install
   node bug-workflow.js
   ```

2. **Test Python version:**
   ```bash
   pip install -r requirements.txt
   python bug_workflow.py
   ```

3. **Test Dashboard:**
   - Open `dashboard.html` in browser
   - Click "Run workflow now" button
   - Watch the simulation

4. **Check your Jira:**
   - Verify a test bug was marked "In Progress"

5. **Check your Claude API logs:**
   - Verify API calls were made

If all tests pass, you're ready for production!

---

## 💰 Cost Estimate (Monthly)

| Service | Free Tier | Cost/Month |
|---------|-----------|-----------|
| Jira Cloud | 10 users | $50 (your existing subscription) |
| Claude API | - | ~$5-50 (depends on bug volume) |
| GitHub Actions | 2000 min/month | Free with your plan |
| Total | - | **~$50-100** |

**Cost optimization tips:**
- Use Claude Haiku instead of Opus (95% cheaper)
- Run less frequently (every 2-4 hours instead of hourly)
- Only process high-priority bugs

---

## 🐛 Troubleshooting

**"Authentication failed" error:**
- ✓ Check Jira API token is correct
- ✓ Verify email address matches Jira account
- ✓ Make sure token hasn't expired

**"No bugs found" but bugs exist:**
- ✓ Check JIRA_PROJECT_KEY matches your project
- ✓ Verify bug status is "Open" (not closed/resolved)
- ✓ Check created date is recent (within 1 hour)

**Claude API errors:**
- ✓ Verify Claude API key is correct
- ✓ Check you have API credits available
- ✓ Reduce bug processing if rate-limited

**Dashboard not updating:**
- ✓ Open in fresh browser window
- ✓ Clear browser cache
- ✓ Check browser console for errors (F12)

**Still stuck?**
- Read `DEPLOYMENT_GUIDE.md` for detailed help
- Check logs for error messages
- Run with `LOG_LEVEL=debug` for verbose output

---

## 🚀 Next Steps

1. **Get API Keys** (5 min) ← START HERE
2. **Create `.env` file** (2 min)
3. **Test locally** (5 min) - Run `node bug-workflow.js` or `python bug_workflow.py`
4. **Deploy** (5-10 min) - Choose GitHub Actions, Docker, or Cron
5. **Monitor** - Open dashboard and watch it work!
6. **Integrate** - Connect to Slack, GitHub, etc. (optional)

---

## 📚 Documentation

- **`bug_workflow_implementation.md`** - Deep dive into the code
- **`DEPLOYMENT_GUIDE.md`** - All deployment options explained
- **`dashboard.html`** - Self-contained web interface

---

## 💡 Pro Tips

1. **Slack Integration** - Add notifications when bugs are processed
2. **GitHub Integration** - Auto-create PRs with generated code
3. **Cost Optimization** - Use Haiku model for 95% cost reduction
4. **Higher Volume** - Set up database for better scaling
5. **CI/CD Integration** - Integrate with your build pipeline

---

## Support

- **Questions?** Check the documentation files
- **Bugs?** Create an issue with logs
- **Need help?** Review the DEPLOYMENT_GUIDE.md

---

## What to Do Now

1. ✅ Save all files to your project folder
2. ✅ Get your API keys (Jira + Claude)
3. ✅ Create `.env` file with your credentials
4. ✅ Run `node bug-workflow.js` or `python bug_workflow.py` to test
5. ✅ Deploy using your preferred method (GitHub Actions, Docker, etc.)
6. ✅ Open `dashboard.html` to monitor
7. ✅ Watch your workflow automate bug fixing! 🎉

---

**You're all set! Happy automating! 🚀**

For detailed information, see `DEPLOYMENT_GUIDE.md`
