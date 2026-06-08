# How to Get Your Claude API Key - Step-by-Step Guide

Follow these exact steps to get your Claude API key for code generation:

---

## ✅ Step 1: Sign Up for Claude Console (If You Don't Have Account)

1. Go to: https://console.anthropic.com/
2. Click **"Sign up"** or **"Log in"**
3. Use your email address
4. Complete the sign-up process

---

## ✅ Step 2: Go to API Keys Page

1. Once logged in, look at the left sidebar
2. Click **"API keys"** or go directly to:
   ```
   https://console.anthropic.com/api-keys
   ```

**You'll see:**
```
┌────────────────────────────────────┐
│ API keys                           │
│                                    │
│ Create a new key                   │
│ [Create key]                       │
│                                    │
│ Workspace API keys                 │
│ Key name     Created    Key        │
│ (no keys yet)                      │
└────────────────────────────────────┘
```

---

## ✅ Step 3: Create New API Key

1. Click the **"Create key"** button
2. A dialog will appear asking for a key name
3. Enter a name: `Bug Automation Workflow`
4. Click **"Create key"**

**You'll see:**
```
┌──────────────────────────────────┐
│ Create a new API key             │
│                                  │
│ Key name:                        │
│ [Bug Automation Workflow______]  │
│                                  │
│                       [Create]   │
└──────────────────────────────────┘
```

---

## ✅ Step 4: Copy Your API Key

⚠️ **CRITICAL:** The key will only be shown ONCE!

1. Your new key will appear: `sk-ant-xxxxxxxxxxxxxxxxxx`
2. Click **"Copy"** button immediately
3. **Save it somewhere safe right now** (password manager, etc.)

**You'll see:**
```
┌──────────────────────────────────┐
│ API Key Created                  │
│                                  │
│ sk-ant-a7b8c9d0e1f2g3h4i5j6k7l  │
│                          [Copy]  │
│                                  │
│ ⚠️  This is the only time you'll │
│    see this key. Save it now!    │
│                   [I saved it ✓] │
└──────────────────────────────────┘
```

---

## ✅ Step 5: Close Dialog

1. Click **"I saved it ✓"** or close the dialog
2. You're done! Your API key is ready.

---

## 💰 Check Your Credits

Before using the API, check if you have credits:

1. Go to: https://console.anthropic.com/account/overview
2. Look for "Credits" or "Usage"
3. You get free credits to start ($5-10)
4. If you need more, add a payment method

---

## 🧪 Test Your Claude API Key

Test your API key with this command:

### Using Python:

```python
import requests
import json

api_key = "sk-ant-xxxxxxxxxxxxx"  # Your API key here

response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    },
    json={
        "model": "claude-opus-4-1",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello, API is working!' in one sentence."
            }
        ]
    }
)

if response.status_code == 200:
    print("✓ API key is working!")
    result = response.json()
    print("Response:", result['content'][0]['text'])
else:
    print("✗ API key failed!")
    print("Error:", response.text)
```

### Using Node.js:

```javascript
const axios = require('axios');

const apiKey = "sk-ant-xxxxxxxxxxxxx"; // Your API key here

axios.post('https://api.anthropic.com/v1/messages', {
  model: 'claude-opus-4-1',
  max_tokens: 100,
  messages: [
    {
      role: 'user',
      content: "Say 'Hello, API is working!' in one sentence."
    }
  ]
}, {
  headers: {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
  }
})
.then(response => {
  console.log('✓ API key is working!');
  console.log('Response:', response.data.content[0].text);
})
.catch(error => {
  console.log('✗ API key failed!');
  console.log('Error:', error.response.data);
});
```

### Using curl:

```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-xxxxxxxxxxxxx" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-4-1",
    "max_tokens": 100,
    "messages": [
      {
        "role": "user",
        "content": "Say hello in one sentence."
      }
    ]
  }'
```

**If successful:**
```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello, API is working!"
    }
  ],
  ...
}
```

---

## 📝 Add to Your .env File

Add your Claude API key to your `.env` file:

```bash
# Existing Jira settings
JIRA_API_URL=https://biswajitpaulckp2010.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=atk_xxxxxxxxxxxx
JIRA_PROJECT_KEY=SCRUM

# Add Claude API key
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
```

⚠️ **SECURITY:**
- ❌ Never share your API key
- ❌ Never commit `.env` to git
- ❌ Never post it online or in screenshots
- ✅ Treat it like a password
- ✅ Use GitHub Secrets for CI/CD

---

## 🔐 If You Accidentally Exposed Your Key

1. Go to: https://console.anthropic.com/api-keys
2. Find the exposed key in the list
3. Click the **"..." menu** or **"Delete"** button
4. Confirm deletion
5. Create a new key

---

## 💰 Choosing the Right Claude Model

Your workflow can use different Claude models. Here's the breakdown:

### For Cost Optimization:

**Claude 3 Haiku** (Fastest, Cheapest)
- **Cost:** ~80% cheaper than Opus
- **Speed:** ~2-3 seconds per bug
- **Quality:** Good for simple bugs
- **Use when:** Processing high volume, simple bugs

```bash
CLAUDE_MODEL=claude-3-5-haiku-20241022
```

### Balanced (Recommended):

**Claude 3.5 Sonnet** (Best balance)
- **Cost:** Medium
- **Speed:** ~10-15 seconds per bug
- **Quality:** Excellent for most bugs
- **Use when:** Default choice, good balance

```bash
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

### Best Quality:

**Claude 3 Opus** (Slowest, Most Expensive)
- **Cost:** ~10x more than Haiku
- **Speed:** ~30+ seconds per bug
- **Quality:** Best possible solutions
- **Use when:** Critical bugs, complex problems

```bash
CLAUDE_MODEL=claude-3-opus-20250219
```

**Recommendation for your workflow:**
```bash
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Best balance
```

---

## 📊 Estimate Costs

Processing 24 bugs/week with different models:

| Model | Cost/100 bugs | Cost/week (24 bugs) | Cost/month |
|-------|--------------|-------------------|-----------|
| Haiku | ~$0.50 | ~$0.12 | ~$0.50 |
| Sonnet | ~$2.40 | ~$0.58 | ~$2.40 |
| Opus | ~$10.00 | ~$2.40 | ~$10.00 |

**Total monthly cost with Sonnet:** ~$2-5 (basically free!)

---

## 🐛 Troubleshooting API Key

### Problem: "401 Unauthorized"
- ✓ Check API key is copied completely (starts with `sk-ant-`)
- ✓ Verify you're using correct API endpoint: `https://api.anthropic.com/v1/messages`
- ✓ Check header format: `x-api-key` (not `X-API-Key`)

### Problem: "Invalid request body"
- ✓ Make sure `model` name is correct
- ✓ Check `max_tokens` is a number
- ✓ Verify `messages` array format

### Problem: "Rate limit exceeded"
- ✓ Add delays between API calls (2-3 seconds)
- ✓ Process fewer bugs per run
- ✓ Upgrade to paid account for higher limits

### Problem: "No credits"
- ✓ Go to https://console.anthropic.com/account/billing/overview
- ✓ Add payment method to get more credits
- ✓ Or wait for free trial credits to reset

---

## ✅ Checklist - Ready to Go?

- [ ] Claude API key created and copied
- [ ] API key tested (optional but recommended)
- [ ] API key added to `.env` file
- [ ] Jira API key also added to `.env`
- [ ] `.env` file is in `.gitignore`
- [ ] Have credits available (check console)

---

## 🚀 Next Steps

1. ✓ Get Jira API key (see GET_JIRA_API_KEY.md)
2. ✓ Get Claude API key (this file)
3. Create `.env` file with both keys
4. Test the workflow:
   ```bash
   python bug_workflow.py
   ```
5. Deploy to your preferred platform
6. Watch it work! 🎉

---

## 📚 Resources

- **Claude API Documentation:** https://docs.anthropic.com/
- **Claude Models:** https://docs.anthropic.com/en/docs/about-claude/models/latest
- **API Pricing:** https://www.anthropic.com/pricing/claude
- **Account Settings:** https://console.anthropic.com/account/overview

---

**Got both API keys? Time to create your .env file!**

Next: Create `.env` file with all values, then test with `python bug_workflow.py`
