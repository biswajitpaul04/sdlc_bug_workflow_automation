#!/usr/bin/env python3
"""
Automated Bug Checking and Code Generation Workflow
With proper logging to file for dashboard
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Configure logging - BOTH to file AND console
log_file = os.path.join('logs', 'workflow.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # Save to file
        logging.StreamHandler()  # Print to console
    ]
)
logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def get_new_bugs(self, project_key: str) -> List[Dict]:
        """Fetch bugs with "To Do" status from project"""
        try:
            jql = f'project = {project_key} AND status = "To Do" ORDER BY created DESC'
            logger.info(f"JQL Query: {jql}")
            
            response = self.session.get(
                f'{self.base_url}/rest/api/3/search/jql',
                params={
                    'jql': jql,
                    'maxResults': 50,
                    'fields': ['key', 'summary', 'description', 'assignee', 'priority', 'labels', 'issuetype']
                }
            )
            response.raise_for_status()
            
            bugs = []
            issues = response.json().get('issues', [])
            logger.info(f"Received {len(issues)} total issues from Jira")
            
            for idx, issue in enumerate(issues):
                try:
                    logger.info(f"Processing issue {idx+1}: {issue.get('key', 'UNKNOWN')}")
                    
                    key = issue.get('key', 'UNKNOWN')
                    fields = issue.get('fields', {})
                    
                    if not fields:
                        logger.warning(f"Issue {key} has no fields!")
                        continue
                    
                    summary = fields.get('summary', 'No summary')
                    description = self._extract_description(fields.get('description'))
                    priority = fields.get('priority', {})
                    priority_name = priority.get('name', 'Medium') if priority else 'Medium'
                    assignee = fields.get('assignee', {})
                    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                    
                    bug = {
                        'key': key,
                        'summary': summary,
                        'description': description,
                        'priority': priority_name,
                        'assignee': assignee_name,
                    }
                    bugs.append(bug)
                    logger.info(f"✓ Successfully parsed: {key}")
                    
                except Exception as e:
                    logger.error(f"Error parsing issue {idx}: {e}")
                    continue
            
            logger.info(f"Found {len(bugs)} issues with 'To Do' status")
            return bugs
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch bugs from Jira: {e}")
            raise
    
    def mark_in_progress(self, issue_key: str, transition_id: str = '11') -> bool:
        """Mark a bug as In Progress"""
        try:
            logger.info(f"Marking {issue_key} as In Progress...")
            response = self.session.post(
                f'{self.base_url}/rest/api/3/issue/{issue_key}/transitions',
                json={'transition': {'id': transition_id}}
            )
            response.raise_for_status()
            logger.info(f"✓ Marked {issue_key} as In Progress")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update bug {issue_key}: {e}")
            return False
    
    @staticmethod
    def _extract_description(description_obj: Optional[Dict]) -> str:
        """Extract plain text from Jira rich text description"""
        if not description_obj:
            return ""
        
        try:
            full_text = ""
            content = description_obj.get('content', []) if isinstance(description_obj, dict) else []
            
            def extract_from_content(items):
                text = ""
                if not items:
                    return text
                    
                for item in items:
                    if isinstance(item, dict):
                        if item.get('type') == 'text' and 'text' in item:
                            text += item['text']
                        elif item.get('type') == 'inlineCard' and 'attrs' in item:
                            url = item['attrs'].get('url', '')
                            text += url
                        if 'content' in item:
                            text += extract_from_content(item['content'])
                
                return text
            
            full_text = extract_from_content(content)
            return full_text.strip() if full_text else ""
            
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return ""


class GitHubClient:
    """Client for fetching HTML files from GitHub"""
    
    @staticmethod
    def extract_github_url(description: str) -> Optional[str]:
        """Extract GitHub URL from bug description"""
        pattern = r'(https?://(?:raw\.)?(?:github\.com|githubusercontent\.com)/[^\s\)]+\.html(?:\?[^\s\)]*)?)'
        match = re.search(pattern, description)
        
        if match:
            url = match.group(1)
            
            if 'github.com' in url and 'raw.' not in url:
                url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            
            url = url.replace('/refs/heads/', '/')
            
            logger.info(f"Found GitHub URL: {url}")
            return url
        
        return None
    
    @staticmethod
    def fetch_html_file(url: str) -> Optional[str]:
        """Fetch HTML file from GitHub with token authentication"""
        try:
            logger.info(f"Fetching HTML from GitHub: {url}")
            
            headers = {}
            if '?token=' in url:
                token = url.split('?token=')[1]
                headers['Authorization'] = f'token {token}'
                url = url.split('?token=')[0]
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"✓ Successfully fetched HTML file ({len(response.text)} bytes)")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch HTML from GitHub: {e}")
            return None


class ClaudeCodeGenerator:
    """Client for generating code solutions using Claude API"""
    
    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-6'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.anthropic.com/v1'
    
    def generate_fixed_html(self, bug: Dict, html_content: Optional[str] = None) -> Optional[str]:
        """Generate fixed HTML code for a bug"""
        try:
            prompt = self._build_prompt(bug, html_content)
            
            logger.info(f"Calling Claude API for {bug['key']} using model {self.model}...")
            
            response = requests.post(
                f'{self.base_url}/messages',
                headers={
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': self.model,
                    'max_tokens': 4096,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            response_text = response.json()['content'][0]['text']
            fixed_html = self._extract_html_from_response(response_text)
            
            if fixed_html:
                logger.info(f"✓ Generated fixed HTML for {bug['key']}")
                return fixed_html
            else:
                logger.error(f"Could not extract HTML from Claude response")
                return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to generate code for {bug['key']}: {e}")
            return None
    
    @staticmethod
    def _extract_html_from_response(response_text: str) -> Optional[str]:
        """Extract HTML from Claude response"""
        html_match = re.search(r'```html\n(.*?)\n```', response_text, re.DOTALL)
        if html_match:
            return html_match.group(1)
        
        if '<!DOCTYPE html' in response_text:
            html_start = response_text.find('<!DOCTYPE html')
            html_end = response_text.rfind('</html>')
            if html_end != -1:
                return response_text[html_start:html_end+7]
        
        return None
    
    @staticmethod
    def _build_prompt(bug: Dict, html_content: Optional[str] = None) -> str:
        """Build prompt for Claude"""
        
        if html_content:
            return f"""You are a senior web developer. A bug has been reported for an HTML file:

**Bug ID:** {bug['key']}
**Title:** {bug['summary']}
**Description:** {bug['description']}
**Priority:** {bug['priority']}

**Current HTML File:**
```html
{html_content}
```

IMPORTANT: You must provide the COMPLETE fixed HTML file.

Analyze the bug and provide the COMPLETE, FIXED HTML code that addresses the issue. 
Return only the full HTML code wrapped in ```html``` markers. No explanations - just the complete fixed code.

The fixed HTML should:
1. Solve the reported bug
2. Maintain all existing functionality
3. Keep the same structure and styling
4. Be production-ready

Return ONLY the complete HTML code wrapped in ```html``` tags."""
        
        else:
            return f"""You are a senior software engineer. A bug has been reported:

**Bug ID:** {bug['key']}
**Title:** {bug['summary']}
**Description:** {bug['description']}
**Priority:** {bug['priority']}

Please analyze the bug and provide suggestions for fixing it."""


class BugWorkflowOrchestrator:
    """Orchestrates the entire bug workflow"""
    
    def __init__(self):
        self.jira = JiraClient(
            base_url=os.getenv('JIRA_API_URL'),
            email=os.getenv('JIRA_EMAIL'),
            api_token=os.getenv('JIRA_API_TOKEN')
        )
        self.generator = ClaudeCodeGenerator(
            api_key=os.getenv('CLAUDE_API_KEY'),
            model=os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-6')
        )
        self.project_key = os.getenv('JIRA_PROJECT_KEY')
        self.fixed_dir = 'fixed_files'
        
        os.makedirs(self.fixed_dir, exist_ok=True)
    
    def run(self) -> Dict:
        """Run the complete workflow"""
        logger.info("=" * 60)
        logger.info("Starting bug workflow...")
        logger.info("=" * 60)
        
        try:
            bugs = self.jira.get_new_bugs(self.project_key)
            
            if not bugs:
                logger.info("No bugs found with 'To Do' status. Exiting.")
                return {'status': 'completed', 'bugs_processed': 0}
            
            processed_count = 0
            for idx, bug in enumerate(bugs, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing bug {idx}/{len(bugs)}: {bug['key']}")
                logger.info(f"{'='*60}")
                
                if self._process_bug(bug):
                    processed_count += 1
                
                import time
                time.sleep(2)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Workflow completed. Processed {processed_count}/{len(bugs)} bugs.")
            logger.info(f"{'='*60}\n")
            return {'status': 'completed', 'bugs_processed': processed_count}
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'failed', 'error': str(e)}
    
    def _process_bug(self, bug: Dict) -> bool:
        """Process a single bug"""
        logger.info(f"Bug: {bug['key']} - {bug['summary']}")
        logger.info(f"Priority: {bug['priority']} | Assigned to: {bug['assignee']}")
        logger.info(f"Description: {bug['description'][:100]}...")
        
        if not self.jira.mark_in_progress(bug['key']):
            return False
        
        logger.info("Step 1/3: Extracting GitHub URL...")
        html_content = None
        github_url = GitHubClient.extract_github_url(bug['description'])
        
        if github_url:
            logger.info(f"✓ GitHub URL found: {github_url}")
            logger.info("Step 2/3: Fetching HTML file from GitHub...")
            html_content = GitHubClient.fetch_html_file(github_url)
            if html_content:
                logger.info(f"✓ HTML file fetched successfully")
            else:
                logger.warning(f"⚠ Could not fetch HTML file, proceeding without context")
        else:
            logger.warning(f"⚠ No GitHub URL found in description")
        
        logger.info("Step 3/3: Generating fixed code with Claude...")
        fixed_html = self.generator.generate_fixed_html(bug, html_content)
        if not fixed_html:
            logger.error(f"✗ Failed to generate code for {bug['key']}")
            return False
        
        self._save_fixed_file(bug['key'], fixed_html, bug['summary'])
        logger.info(f"✓ Bug {bug['key']} processing completed successfully!")
        return True
    
    def _save_fixed_file(self, bug_key: str, fixed_html: str, bug_summary: str) -> None:
        """Save fixed HTML file"""
        try:
            safe_summary = bug_summary.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = os.path.join(self.fixed_dir, f'{bug_key}_{safe_summary}.html')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(fixed_html)
            
            logger.info(f"✓ Fixed file saved: {filename}")
            
        except IOError as e:
            logger.error(f"✗ Failed to save fixed file: {e}")


def main():
    """Main entry point"""
    required_vars = [
        'JIRA_API_URL',
        'JIRA_EMAIL',
        'JIRA_API_TOKEN',
        'JIRA_PROJECT_KEY',
        'CLAUDE_API_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return {'status': 'failed', 'error': 'Missing configuration'}
    
    orchestrator = BugWorkflowOrchestrator()
    result = orchestrator.run()
    
    return result


if __name__ == '__main__':
    result = main()
    exit(0 if result['status'] == 'completed' else 1)