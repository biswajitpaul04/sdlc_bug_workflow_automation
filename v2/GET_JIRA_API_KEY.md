# How to Get Your Jira API Key - Step-by-Step Guide

Your Jira URL: `https://biswajitpaulckp2010.atlassian.net/jira/software/projects/SCRUM/boards/1`

Follow these exact steps to generate your API token:

---

## ✅ Step 1: Go to Atlassian API Token Management

1. Open this link in your browser:
   ```
   https://id.atlassian.com/manage-profile/security/api-tokens
   ```

2. Or manually navigate:
   - Go to your Atlassian profile (your avatar/account icon)
   - Select "Profile"
   - In left menu, click "Security"
   - Or go directly to: https://id.atlassian.com/manage-profile/security/api-tokens

---

## ✅ Step 2: Sign In (If Needed)

- You'll need to sign in with your Atlassian account
- Use the email you use for Jira
- Example: `your-email@company.com`

---

## ✅ Step 3: Create API Token

Once on the API Tokens page:

1. Look for the button **"Create API token"** at the top right
2. Click it
3. A dialog box will appear asking for a label
4. Enter a label (e.g., `Bug Automation Workflow`)
5. Click **"Create"**

**Screenshot (what you'll see):**
```
┌─────────────────────────────────────────────┐
│ API tokens                                  │
│                            [Create API token]│
│                                             │
│ Label              Created     Last used    │
│ Bug Automation...  Jan 15...   -            │
│ My API Token       Dec 20...   Dec 21...    │
└─────────────────────────────────────────────┘
```

---

## ✅ Step 4: Copy Your Token

⚠️ **IMPORTANT:** The token will only be shown ONCE!

1. The new token will appear in a dialog
2. It looks like: `atk_xxxxxxxxxxxxxxxxxxxxxxxx`
3. Click **"Copy"** button or select and copy manually
4. **Save it somewhere safe** (you'll need it in 2 minutes)

**You'll see something like:**
```
┌──────────────────────────────────────────┐
│ Your new API token                       │
│                                          │
│ atk_abc123def456ghi789jkl012mno345pqr   │
│                                   [Copy] │
│                                          │
│ ⚠️  Save this token - you won't see it   │
│    again!                                │
└──────────────────────────────────────────┘
```

---

## ✅ Step 5: Close Dialog

1. After copying, click **"Close"** or press Escape
2. You're done! Your API token is ready.

---

## 📋 Information You Need for the Workflow

Now you have everything needed. Collect these details:

```
JIRA_API_URL = https://biswajitpaulckp2010.atlassian.net
JIRA_EMAIL = your-email@company.com (the email you use for Jira)
JIRA_API_TOKEN = atk_xxxxxxxxxxxxxxxxxxxx (just copied)
JIRA_PROJECT_KEY = SCRUM (from your URL - the project key)
```

---

## 🔑 How to Get Each Value

### 1. JIRA_API_URL
From your URL: `https://biswajitpaulckp2010.atlassian.net/jira/software/projects/SCRUM/boards/1`

**Extract:** `https://biswajitpaulckp2010.atlassian.net`

### 2. JIRA_EMAIL
The email address you use to log into Jira
- Example: `john.smith@company.com`
- Or: `your-username@gmail.com`

### 3. JIRA_API_TOKEN
The token you just copied (atk_...)
- Keep this **SECRET** - don't share it!
- Don't commit it to git

### 4. JIRA_PROJECT_KEY
From your URL: `https://biswajitpaulckp2010.atlassian.net/jira/software/projects/SCRUM/boards/1`

**Extract:** `SCRUM`

Or find it:
1. Go to your Jira project
2. Click "Project settings" (gear icon)
3. Look for "Project key" - it will show `SCRUM`

---

## 🔧 Test Your Credentials

Once you have your API token, test it with this command:

### Using curl (Mac/Linux/Windows PowerShell):

```bash
curl -X GET \
  -H "Authorization: Basic $(echo -n 'your-email@company.com:atk_xxxxxxxxxxxx' | base64)" \
  https://biswajitpaulckp2010.atlassian.net/rest/api/3/myself
```

### Using Python:

```python
import requests
import base64

email = "your-email@company.com"
api_token = "atk_xxxxxxxxxxxx"
url = "https://biswajitpaulckp2010.atlassian.net"

auth_string = base64.b64encode(f"{email}:{api_token}".encode()).decode()

response = requests.get(
    f"{url}/rest/api/3/myself",
    headers={"Authorization": f"Basic {auth_string}"}
)

if response.status_code == 200:
    print("✓ Authentication successful!")
    print(response.json())
else:
    print("✗ Authentication failed!")
    print(response.text)
```

### Using Node.js:

```javascript
const axios = require('axios');

const email = "your-email@company.com";
const apiToken = "atk_xxxxxxxxxxxx";
const url = "https://biswajitpaulckp2010.atlassian.net";

const auth = Buffer.from(`${email}:${apiToken}`).toString('base64');

axios.get(`${url}/rest/api/3/myself`, {
  headers: {
    'Authorization': `Basic ${auth}`
  }
})
.then(response => {
  console.log('✓ Authentication successful!');
  console.log(response.data);
})
.catch(error => {
  console.log('✗ Authentication failed!');
  console.log(error.response.data);
});
```

**If successful, you'll see your Jira user info:**
```json
{
  "accountId": "abc123def456",
  "emailAddress": "your-email@company.com",
  "displayName": "Your Name",
  ...
}
```

---

## 📝 Create Your .env File

Now create a `.env` file in your project with these values:

```bash
# Copy this into a file called .env
JIRA_API_URL=https://biswajitpaulckp2010.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=atk_xxxxxxxxxxxx
JIRA_PROJECT_KEY=SCRUM
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
```

⚠️ **SECURITY WARNINGS:**
- ❌ Never commit `.env` to git
- ❌ Never share your API token
- ❌ Never post it online
- ✅ Keep it in a password manager
- ✅ Use GitHub Secrets if deploying to GitHub Actions

---

## 🔐 If You Accidentally Exposed Your Token

1. Go back to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Find the exposed token in the list
3. Click the **"..." menu** next to it
4. Select **"Delete"**
5. Create a new token with a different name

---

## 🐛 Troubleshooting API Token

### Problem: "Cannot find Create API token button"
- ✓ Make sure you're logged in
- ✓ Check you're at https://id.atlassian.com/manage-profile/security/api-tokens
- ✓ Try clearing browser cache and refreshing

### Problem: "Token not working - 401 Unauthorized"
- ✓ Make sure you copied the entire token (atk_...)
- ✓ Verify your email is correct
- ✓ Check token hasn't expired (try creating a new one)
- ✓ Make sure you have access to the SCRUM project

### Problem: "Cannot access project SCRUM"
- ✓ Verify your user has permission to access SCRUM project
- ✓ Ask your Jira admin to grant access
- ✓ Check project key is spelled correctly: `SCRUM` (not `scrum`)

---

## 📚 Additional Resources

- **Atlassian API Token Docs:** https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
- **Jira Cloud API Docs:** https://developer.atlassian.com/cloud/jira/rest/v3/
- **Authorization Methods:** https://developer.atlassian.com/cloud/jira/platform/jira-rest-api-authentication/

---

## ✅ Checklist - You're Ready When:

- [ ] API token created and copied
- [ ] Email address confirmed
- [ ] Project key is `SCRUM`
- [ ] Jira URL is `https://biswajitpaulckp2010.atlassian.net`
- [ ] Tested credentials (optional but recommended)
- [ ] `.env` file created with all values
- [ ] `.env` is in `.gitignore` (if using git)

---

## 🚀 Next Steps

Once you have your Jira API token:

1. Create Claude API key (same process as Jira)
2. Add both to your `.env` file
3. Run the workflow test:
   ```bash
   python bug_workflow.py
   ```
4. Check your Jira - the test bug should be marked "In Progress"
5. Deploy your workflow!

---

**Questions?** Check the DEPLOYMENT_GUIDE.md or QUICKSTART.md files!

Last updated: January 2024
