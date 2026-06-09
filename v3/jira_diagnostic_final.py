#!/usr/bin/env python3
"""
Final Diagnostic - Test Project Issues Endpoints
When /search is disabled, try /project/.../issues
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import json

load_dotenv()

JIRA_URL = os.getenv('JIRA_API_URL', '').rstrip('/')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SCRUM')

print("=" * 70)
print("FINAL DIAGNOSTIC - Project Issues Endpoints")
print("=" * 70)

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

# Test project issues endpoints
endpoints = [
    # Project issues endpoints
    (f"/rest/api/3/projects/{PROJECT_KEY}/issues", "v3 project issues", {'maxResults': 50}),
    (f"/rest/api/2/projects/{PROJECT_KEY}/issues", "v2 project issues", {'maxResults': 50}),
    
    # Issue navigator
    (f"/issues", "Issue navigator", {'project': PROJECT_KEY, 'status': 'To Do'}),
    
    # Backlog endpoints (Scrum specific)
    (f"/rest/agile/1.0/board", "Agile board", {}),
    (f"/rest/agile/1.0/board/1/issues", "Agile board issues", {'jql': f'project = {PROJECT_KEY}'}),
    
    # Component endpoints
    (f"/rest/api/3/project/{PROJECT_KEY}/components", "Project components", {}),
    
    # Issue type endpoint
    (f"/rest/api/3/issuetype", "Issue types", {}),
    
    # Alternative: Get board and issues from there
    (f"/rest/greenhopper/1.0/xboard/plan/backlog/data", "GreenHopper backlog", {}),
]

print("\n[Testing Project Issues Endpoints]")
print("-" * 70)

working_endpoints = []

for endpoint, description, params in endpoints:
    url = f"{JIRA_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, auth=auth, timeout=5)
        
        status = response.status_code
        if status == 200:
            print(f"✓ {description:30} - SUCCESS (200)")
            print(f"  Endpoint: {endpoint}")
            working_endpoints.append((endpoint, description, params))
            
            # Try to extract useful info
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'issues' in data:
                        print(f"  Issues found: {len(data.get('issues', []))}")
                        if data['issues']:
                            issue = data['issues'][0]
                            print(f"  First issue: {issue.get('key')} - {issue.get('summary', 'N/A')}")
                    if 'values' in data:
                        print(f"  Items found: {len(data.get('values', []))}")
                    if 'issues' in data and isinstance(data['issues'], list):
                        for issue in data['issues'][:3]:
                            print(f"    - {issue.get('key')}")
            except:
                print(f"  (Could not parse response)")
            print()
        
        elif status == 401:
            print(f"⚠ {description:30} - UNAUTHORIZED (401)\n")
        elif status == 403:
            print(f"⚠ {description:30} - FORBIDDEN (403)\n")
        elif status == 404:
            print(f"⚠ {description:30} - NOT FOUND (404)\n")
        elif status == 405:
            print(f"⚠ {description:30} - METHOD NOT ALLOWED (405)\n")
        elif status == 410:
            print(f"⚠ {description:30} - GONE (410)\n")
        else:
            print(f"⚠ {description:30} - Status {status}\n")
    
    except requests.exceptions.Timeout:
        print(f"⚠ {description:30} - TIMEOUT\n")
    except Exception as e:
        print(f"⚠ {description:30} - ERROR: {e}\n")

print("=" * 70)
print("[RESULTS]")
print("-" * 70)

if working_endpoints:
    print(f"✓ Found {len(working_endpoints)} working endpoint(s)!\n")
    
    for endpoint, description, params in working_endpoints:
        print(f"  • {description}")
        print(f"    {endpoint}\n")
    
    # Check which one is best for getting issues
    issues_endpoints = [e for e in working_endpoints if 'issues' in e[0].lower()]
    
    if issues_endpoints:
        print("\n✓ BEST OPTION: Issues endpoint found!\n")
        for endpoint, description, params in issues_endpoints:
            print(f"Use this endpoint: {endpoint}")
            print(f"Description: {description}\n")
    else:
        print("\n⚠ No direct issues endpoint found")
        print("But you CAN access project info")
        print("You may need to:")
        print("  1. Use Jira UI scraping")
        print("  2. Or ask admin to enable search API\n")

else:
    print("❌ No working issues endpoints found!\n")
    
    print("Your Jira instance has search API completely disabled.")
    print("\nOptions:")
    print("  1. Ask Jira admin to enable /rest/api/3/search")
    print("  2. Or grant your user search permissions")
    print("  3. Or manually export issues from Jira UI as CSV")
    print("  4. Or use Jira UI scraping (not recommended)\n")

print("=" * 70)
print("[NEXT STEPS]")
print("-" * 70)

if working_endpoints and any('issues' in e[0].lower() for e in working_endpoints):
    print("\n✓ Great news! An issues endpoint works!\n")
    
    working_issue_ep = [e for e in working_endpoints if 'issues' in e[0].lower()][0]
    endpoint = working_issue_ep[0]
    
    print("You need to update your code to use this endpoint.")
    print(f"\nEndpoint: {endpoint}\n")
    
    print("Code update needed in bug_workflow_claude_FIXED.py:")
    print("-" * 70)
    print(f"""
# In the get_new_bugs method, replace:
url = f'{{self.base_url}}/rest/api/3/search'

# With:
url = f'{{self.base_url}}{endpoint}'

# Full code example:
response = self.session.get(
    f'{{self.base_url}}{endpoint}',
    params={{'maxResults': 50, 'fields': ['key', 'summary', 'description', 'assignee', 'priority']}},
    timeout=10
)
""")

else:
    print("\n❌ No search endpoints available on your instance.\n")
    print("This Jira instance has the search API completely disabled.")
    print("\nYour options:")
    print("\n1. Ask your Jira admin to enable the search API")
    print("   - They need to enable /rest/api/3/search endpoint")
    print("   - Or grant your user search permissions\n")
    
    print("2. Use manual workaround:")
    print("   - Go to: https://biswajitpaulckp2010.atlassian.net/issues")
    print("   - Filter to project = SCRUM and status = To Do")
    print("   - Export as CSV")
    print("   - Feed CSV to the workflow script\n")
    
    print("3. Use Jira Cloud if possible")
    print("   - This version appears to be custom/dev")
    print("   - Jira Cloud has full API support\n")

print("=" * 70)
