# Automated Bug Workflow - Complete Implementation Guide

## Architecture Overview

This workflow runs on an hourly schedule and performs these steps:
1. Triggered by scheduler (cron, GitHub Actions, cloud function, Jenkins)
2. Queries Jira API for new bugs
3. Updates bug status to "In Progress"
4. Generates code solutions using Claude API
5. Logs results and handles errors

---

## Part 1: Scheduling Options

### Option A: GitHub Actions (Recommended for cloud)
**File: `.github/workflows/bug-checker.yml`**
```yaml
name: Hourly Bug Checker

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Manual trigger option

jobs:
  check-and-generate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm install axios dotenv
      
      - name: Run bug workflow
        env:
          JIRA_API_URL: ${{ secrets.JIRA_API_URL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT_KEY }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: node bug-workflow.js
      
      - name: Send Slack notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Bug workflow completed",
              "status": "${{ job.status }}"
            }
```

### Option B: Cron Job (Local/Self-hosted)
**File: `setup-cron.sh`**
```bash
#!/bin/bash

# Install the cron job
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bug-workflow.js"
CRON_JOB="0 * * * * cd $SCRIPT_PATH/.. && /usr/bin/node bug-workflow.js >> /var/log/bug-workflow.log 2>&1"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -q "bug-workflow.js") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job installed: runs every hour"
```

### Option C: Cloud Functions (AWS Lambda, Google Cloud Functions, Azure Functions)
**Example: Google Cloud Functions (Python)**
```python
import functions_framework
from google.cloud import tasks_v2
import json

@functions_framework.http
def trigger_bug_workflow(request):
    """HTTP Cloud Function to trigger bug workflow"""
    from bug_workflow import main
    
    result = main()
    return {"status": "success", "bugs_processed": result}

# Scheduled via Cloud Scheduler to hit this endpoint every hour
```

---

## Part 2: Main Workflow Script

**File: `bug-workflow.js`** (Node.js implementation)

```javascript
require('dotenv').config();
const axios = require('axios');

const config = {
  jiraApiUrl: process.env.JIRA_API_URL,
  jiraApiToken: process.env.JIRA_API_TOKEN,
  jiraProjectKey: process.env.JIRA_PROJECT_KEY,
  claudeApiKey: process.env.CLAUDE_API_KEY,
};

const logger = {
  log: (msg) => console.log(`[${new Date().toISOString()}] ${msg}`),
  error: (msg) => console.error(`[${new Date().toISOString()}] ERROR: ${msg}`),
};

// ============================================
// STEP 1: Check for new bugs in Jira
// ============================================
async function getNewBugsFromJira() {
  try {
    // Query bugs created in the last 1 hour
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    const jql = `project = ${config.jiraProjectKey} AND type = Bug AND status = Open AND created >= "${oneHourAgo.toISOString()}"`;
    
    const response = await axios.get(
      `${config.jiraApiUrl}/rest/api/3/search`,
      {
        params: {
          jql: jql,
          maxResults: 50,
          fields: ['key', 'summary', 'description', 'assignee', 'priority', 'labels'],
        },
        auth: {
          username: process.env.JIRA_EMAIL,
          password: config.jiraApiToken,
        },
      }
    );

    const bugs = response.data.issues.map(issue => ({
      key: issue.key,
      summary: issue.fields.summary,
      description: issue.fields.description?.content?.[0]?.content?.[0]?.text || '',
      priority: issue.fields.priority?.name || 'Medium',
      assignee: issue.fields.assignee?.displayName || 'Unassigned',
      labels: issue.fields.labels || [],
    }));

    logger.log(`Found ${bugs.length} new bugs`);
    return bugs;
  } catch (error) {
    logger.error(`Failed to fetch bugs from Jira: ${error.message}`);
    throw error;
  }
}

// ============================================
// STEP 2: Mark bug as "In Progress"
// ============================================
async function markBugInProgress(bugKey) {
  try {
    const response = await axios.post(
      `${config.jiraApiUrl}/rest/api/3/issue/${bugKey}/transitions`,
      {
        transition: {
          id: '3', // ID for "In Progress" transition (verify in your Jira)
        },
      },
      {
        auth: {
          username: process.env.JIRA_EMAIL,
          password: config.jiraApiToken,
        },
      }
    );

    logger.log(`Marked ${bugKey} as In Progress`);
    return true;
  } catch (error) {
    logger.error(`Failed to update bug ${bugKey}: ${error.message}`);
    return false;
  }
}

// ============================================
// STEP 3: Generate code with Claude API
// ============================================
async function generateCodeSolution(bug) {
  try {
    const prompt = `
You are a code generation assistant. A bug has been reported:

Bug ID: ${bug.key}
Title: ${bug.summary}
Description: ${bug.description}
Priority: ${bug.priority}
Labels: ${bug.labels.join(', ')}

Please provide:
1. Root cause analysis
2. Code fix (in the appropriate language)
3. Test cases to verify the fix
4. Deployment notes

Format as markdown with code blocks.
    `;

    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        model: 'claude-opus-4-1',
        max_tokens: 2048,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
      },
      {
        headers: {
          'x-api-key': config.claudeApiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
      }
    );

    const generatedCode = response.data.content[0].text;
    logger.log(`Generated code solution for ${bug.key}`);
    return generatedCode;
  } catch (error) {
    logger.error(`Failed to generate code for ${bug.key}: ${error.message}`);
    return null;
  }
}

// ============================================
// STEP 4: Save results to a file or database
// ============================================
async function saveResults(bugKey, solution) {
  try {
    const fs = require('fs').promises;
    const timestamp = new Date().toISOString();
    const filename = `solutions/${bugKey}_${timestamp.replace(/[:.]/g, '-')}.md`;
    
    const content = `# Bug Fix: ${bugKey}
Generated: ${timestamp}

## Solution
${solution}
    `;

    await fs.mkdir('solutions', { recursive: true });
    await fs.writeFile(filename, content);
    logger.log(`Solution saved to ${filename}`);
  } catch (error) {
    logger.error(`Failed to save results: ${error.message}`);
  }
}

// ============================================
// MAIN WORKFLOW
// ============================================
async function main() {
  logger.log('Starting bug workflow...');
  
  try {
    // Get new bugs
    const bugs = await getNewBugsFromJira();
    
    if (bugs.length === 0) {
      logger.log('No new bugs found. Exiting.');
      return { status: 'completed', bugsProcessed: 0 };
    }

    // Process each bug
    let processedCount = 0;
    for (const bug of bugs) {
      logger.log(`Processing bug: ${bug.key}`);
      
      // Mark as In Progress
      const updated = await markBugInProgress(bug.key);
      if (!updated) continue;
      
      // Generate code
      const solution = await generateCodeSolution(bug);
      if (solution) {
        await saveResults(bug.key, solution);
        processedCount++;
      }
      
      // Rate limiting - avoid hitting API limits
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    logger.log(`Workflow completed. Processed ${processedCount} bugs.`);
    return { status: 'completed', bugsProcessed: processedCount };
  } catch (error) {
    logger.error(`Workflow failed: ${error.message}`);
    process.exit(1);
  }
}

// Run the workflow
if (require.main === module) {
  main();
}

module.exports = { main };
```

---

## Part 3: Environment Configuration

**File: `.env`**
```bash
# Jira Configuration
JIRA_API_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PROJ

# Claude API
CLAUDE_API_KEY=sk-ant-...

# Optional: For production logging
LOG_LEVEL=info
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

**File: `.env.example`** (commit this, not .env)
```bash
JIRA_API_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PROJ
CLAUDE_API_KEY=sk-ant-...
LOG_LEVEL=info
```

---

## Part 4: Enhanced Features & Best Practices

### 4.1 Error Handling & Retry Logic
```javascript
async function withRetry(fn, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      logger.log(`Attempt ${i + 1} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
}
```

### 4.2 Notification System
```javascript
async function sendNotification(bugKey, solution, status) {
  const slack_message = {
    text: `Bug ${bugKey} processed`,
    blocks: [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Bug:* ${bugKey}\n*Status:* ${status}`,
        },
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `\`\`\`${solution.substring(0, 300)}...\`\`\``,
        },
      },
    ],
  };

  await axios.post(process.env.SLACK_WEBHOOK, slack_message);
}
```

### 4.3 Database Logging (Optional)
```javascript
// Save to MongoDB or PostgreSQL
async function logToDatabase(bugKey, solution, executionTime) {
  const db = require('./db-connection');
  
  await db.collection('bug_solutions').insertOne({
    bugKey,
    solutionLength: solution.length,
    executionTime,
    createdAt: new Date(),
    status: 'completed',
  });
}
```

### 4.4 Monitoring & Metrics
```javascript
const startTime = Date.now();
// ... workflow execution ...
const executionTime = Date.now() - startTime;

logger.log(`Workflow execution time: ${executionTime}ms`);
// Send to CloudWatch, Datadog, or similar
```

---

## Part 5: Jira API Reference

### Find Transition ID for "In Progress"
```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-domain.atlassian.net/rest/api/3/issue/BUG-123/transitions
```

Look for the transition with `"name": "In Progress"` and note its `id`.

### JQL Query Examples
```
# Bugs created in last hour
created >= -1h

# High priority bugs
priority = Highest OR priority = High

# Unassigned bugs
assignee IS EMPTY

# Bugs with specific label
labels = backend

# Combined
project = PROJ AND type = Bug AND status = Open AND created >= -1h AND priority >= High
```

---

## Part 6: Deployment Checklist

- [ ] Create `.env` file with all secrets (never commit)
- [ ] Set environment variables in GitHub Secrets / Cloud Platform
- [ ] Test workflow manually first: `node bug-workflow.js`
- [ ] Verify Jira API token works: Test API calls
- [ ] Verify Claude API key works: Test API calls
- [ ] Find correct transition ID for "In Progress" in your Jira
- [ ] Set up Slack webhook for notifications (optional)
- [ ] Enable GitHub Actions / Cloud Scheduler
- [ ] Set up monitoring/alerts for workflow failures
- [ ] Create log files directory: `mkdir -p logs`
- [ ] Test with one bug before going live

---

## Part 7: Troubleshooting

### Bug not transitioning status
- Verify transition ID is correct for your Jira workflow
- Check user has permission to change status
- Ensure bug isn't already in In Progress

### Jira API authentication fails
- Verify API token is valid (regenerate if needed)
- Check email address is correct
- Ensure URL includes `/rest/api/3/` endpoint

### Claude API rate limits
- Add exponential backoff between requests
- Process fewer bugs per cycle if needed
- Use `claude-haiku` for faster/cheaper generations

### High execution time
- Limit number of bugs processed per run
- Use async processing with queues
- Consider splitting into multiple smaller workflows

---

## Part 8: Future Enhancements

1. **ML-based bug categorization**: Use Claude to categorize bugs before code generation
2. **Automated PR creation**: Auto-create pull requests with generated code
3. **Cost optimization**: Route simple bugs to Claude Haiku, complex ones to Opus
4. **Feedback loop**: Track which generated solutions were actually used/merged
5. **Multi-repository support**: Process bugs across multiple projects
6. **Smart scheduling**: Process higher priority bugs immediately, others on schedule
7. **Dashboard**: Web UI to view bug processing status and solutions
8. **Integration with other tools**: Create tickets in GitHub, GitLab, Linear, etc.

---

## Support & Resources

- Jira API Docs: https://developer.atlassian.com/cloud/jira/rest/v3/
- Claude API Docs: https://docs.anthropic.com/en/docs/about-claude/models/latest
- GitHub Actions: https://docs.github.com/en/actions
- Cron Expression Format: https://crontab.guru/

