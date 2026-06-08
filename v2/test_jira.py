import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials
jira_url = os.getenv('JIRA_API_URL')
email = os.getenv('JIRA_EMAIL')
token = os.getenv('JIRA_API_TOKEN')

print(f"Testing Jira Connection...")
print(f"URL: {jira_url}")
print(f"Email: {email}")
print(f"Token: {token[:10]}..." if token else "Token: MISSING")
print()

# Test 1: Check if basic auth works
print("=" * 50)
print("Test 1: Basic Authentication")
print("=" * 50)

try:
    response = requests.get(
        f"{jira_url}/rest/api/3/myself",
        auth=(email, token)
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ SUCCESS! Authenticated as: {user.get('displayName')}")
        print(f"   Account ID: {user.get('accountId')}")
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 2: Try simple search using NEW endpoint
print("=" * 50)
print("Test 2: Search (Simple Query) - NEW ENDPOINT")
print("=" * 50)

try:
    response = requests.get(
        f"{jira_url}/rest/api/3/search/jql",
        params={'maxResults': 1},
        auth=(email, token)
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Found {data.get('total')} total issues")
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 3: Try with JQL query using NEW endpoint
print("=" * 50)
print("Test 3: Search with JQL - NEW ENDPOINT")
print("=" * 50)

try:
    jql = "project = SCRUM AND status = To Do"
    print(f"JQL: {jql}")
    
    response = requests.get(
        f"{jira_url}/rest/api/3/search/jql",
        params={
            'jql': jql,
            'maxResults': 5,
            'fields': ['key', 'summary', 'issuetype']
        },
        auth=(email, token)
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Found {len(data.get('issues', []))} open issues in SCRUM")
        for issue in data.get('issues', []):
            issue_type = issue['fields'].get('issuetype', {}).get('name', 'Unknown')
            print(f"   - {issue['key']} ({issue_type}): {issue['fields']['summary']}")
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 4: Get transitions for an issue (to find correct transition ID)
print("=" * 50)
print("Test 4: Get Issue Transitions")
print("=" * 50)

try:
    # Try to get transitions for SCRUM-2 (or first available issue)
    issue_key = "SCRUM-2"
    print(f"Getting transitions for: {issue_key}")
    
    response = requests.get(
        f"{jira_url}/rest/api/3/issue/{issue_key}/transitions",
        auth=(email, token)
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Available transitions:")
        for transition in data.get('transitions', []):
            print(f"   ID: {transition['id']:3} → {transition['name']}")
    else:
        print(f"❌ FAILED! Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 50)
print("Testing Complete!")
print("=" * 50)