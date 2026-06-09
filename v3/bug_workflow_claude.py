#!/usr/bin/env python3
"""
Automated Bug Checking and Code Generation Workflow
Reads HTML file from GitHub, analyzes bugs, applies fixes, and saves updated HTML
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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
    
    def get_new_bugs(self, project_key: str, hours: int = 1) -> List[Dict]:
        """
        Fetch bugs/tasks with "To Do" status from project
        """
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
                    labels = fields.get('labels', [])
                    issuetype = fields.get('issuetype', {})
                    type_name = issuetype.get('name', 'Unknown') if issuetype else 'Unknown'
                    
                    bug = {
                        'key': key,
                        'summary': summary,
                        'description': description,
                        'priority': priority_name,
                        'assignee': assignee_name,
                        'labels': labels if labels else [],
                        'type': type_name,
                    }
                    bugs.append(bug)
                    logger.info(f"  ✓ Successfully parsed: {key}")
                    
                except Exception as e:
                    logger.error(f"Error parsing issue {idx}: {e}")
                    continue
            
            logger.info(f"Found {len(bugs)} issues with 'To Do' status")
            return bugs
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch bugs from Jira: {e}")
            raise
    
    def mark_in_progress(self, issue_key: str, transition_id: str = '11') -> bool:
        """
        Mark a bug as In Progress
        """
        try:
            response = self.session.post(
                f'{self.base_url}/rest/api/3/issue/{issue_key}/transitions',
                json={'transition': {'id': transition_id}}
            )
            response.raise_for_status()
            logger.info(f"Marked {issue_key} as In Progress")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update bug {issue_key}: {e}")
            return False
    
    @staticmethod
    def _extract_description(description_obj: Optional[Dict]) -> str:
        """Extract plain text and URLs from Jira's rich text description"""
        if not description_obj:
            return ""
        
        try:
            full_text = ""
            content = description_obj.get('content', []) if isinstance(description_obj, dict) else []
            
            # Recursively extract text and URLs from all content blocks
            def extract_from_content(items):
                text = ""
                if not items:
                    return text
                    
                for item in items:
                    if isinstance(item, dict):
                        # Handle text blocks
                        if item.get('type') == 'text' and 'text' in item:
                            text += item['text']
                        # Handle links
                        elif item.get('type') == 'inlineCard' and 'attrs' in item:
                            url = item['attrs'].get('url', '')
                            text += url
                        # Recursively handle nested content
                        if 'content' in item:
                            text += extract_from_content(item['content'])
                
                return text
            
            full_text = extract_from_content(content)
            return full_text.strip() if full_text else ""
            
        except (IndexError, KeyError, TypeError) as e:
            logger.debug(f"Error extracting description: {e}")
            return ""


class GitHubClient:
    """Client for fetching HTML files from GitHub"""
    
    @staticmethod
    def extract_github_url(description: str) -> Optional[str]:
        """
        Extract GitHub URL from bug description
        """
        pattern = r'(https?://(?:raw\.)?(?:github\.com|githubusercontent\.com)/[^\s\)]+\.html(?:\?[^\s\)]*)?)'
        match = re.search(pattern, description)
        
        if match:
            url = match.group(1)
            
            # Convert regular GitHub URL to raw content URL
            if 'github.com' in url and 'raw.' not in url:
                url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            
            # Fix /refs/heads/branch/ format to /branch/
            url = url.replace('/refs/heads/', '/')
            
            logger.info(f"Found GitHub URL: {url}")
            return url
        
        return None
    
    @staticmethod
    def fetch_html_file(url: str) -> Optional[str]:
        """
        Fetch HTML file content from GitHub raw URL
        """
        try:
            logger.info(f"Fetching HTML from GitHub: {url}")
            
            # Extract token from URL if present
            headers = {}
            if '?token=' in url:
                token = url.split('?token=')[1]
                headers['Authorization'] = f'token {token}'
                url = url.split('?token=')[0]
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Successfully fetched HTML file ({len(response.text)} bytes)")
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
        """
        Generate fixed HTML code for a bug
        Returns the complete fixed HTML file
        """
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
            
            # Extract HTML code from response
            fixed_html = self._extract_html_from_response(response_text)
            
            if fixed_html:
                logger.info(f"Generated fixed HTML for {bug['key']}")
                return fixed_html
            else:
                logger.error(f"Could not extract HTML from Claude response")
                return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to generate code for {bug['key']}: {e}")
            return None
    
    @staticmethod
    def _extract_html_from_response(response_text: str) -> Optional[str]:
        """
        Extract HTML code from Claude's response
        Looks for HTML code between ```html``` markers or complete HTML document
        """
        # Try to find HTML in code blocks
        html_match = re.search(r'```html\n(.*?)\n```', response_text, re.DOTALL)
        if html_match:
            return html_match.group(1)
        
        # If no code block, look for complete HTML document
        if '<!DOCTYPE html' in response_text:
            html_start = response_text.find('<!DOCTYPE html')
            html_end = response_text.rfind('</html>')
            if html_end != -1:
                return response_text[html_start:html_end+7]
        
        return None
    
    @staticmethod
    def _build_prompt(bug: Dict, html_content: Optional[str] = None) -> str:
        """Build the prompt for Claude - request complete fixed HTML"""
        
        if html_content:
            return f"""You are a senior web developer. A bug has been reported for an HTML file:

**Bug ID:** {bug['key']}
**Title:** {bug['summary']}
**Description:** {bug['description']}
**Priority:** {bug['priority']}
**Assigned to:** {bug['assignee']}

**Current HTML File:**
```html
{html_content}
```

IMPORTANT: You must provide the COMPLETE fixed HTML file (the entire code). Do NOT provide partial fixes or explanations.

Analyze the bug and provide the COMPLETE, FIXED HTML code that addresses the issue. 
Return only the full HTML code wrapped in ```html``` markers. No explanations, no comments about what changed - just the complete fixed code.

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
        """
        Run the complete workflow
        """
        logger.info("Starting bug workflow...")
        
        try:
            bugs = self.jira.get_new_bugs(self.project_key, hours=1)
            
            if not bugs:
                logger.info("No bugs found with 'To Do' status. Exiting.")
                return {'status': 'completed', 'bugs_processed': 0}
            
            processed_count = 0
            for bug in bugs:
                if self._process_bug(bug):
                    processed_count += 1
                
                import time
                time.sleep(2)
            
            logger.info(f"Workflow completed. Processed {processed_count}/{len(bugs)} bugs.")
            return {'status': 'completed', 'bugs_processed': processed_count}
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'failed', 'error': str(e)}
    
    def _process_bug(self, bug: Dict) -> bool:
        """
        Process a single bug
        """
        logger.info(f"Processing {bug['type']}: {bug['key']}")
        logger.info(f"Bug Summary: {bug['summary']}")
        logger.info(f"Bug Description: {bug['description']}")
        logger.info(f"Priority: {bug['priority']}")
        logger.info(f"Assigned to: {bug['assignee']}")
        
        if not self.jira.mark_in_progress(bug['key']):
            return False
        
        # Try to fetch HTML file from GitHub
        html_content = None
        github_url = GitHubClient.extract_github_url(bug['description'])
        
        if github_url:
            logger.info(f"✅ GitHub URL found: {github_url}")
            html_content = GitHubClient.fetch_html_file(github_url)
        else:
            logger.warning(f"❌ No GitHub URL found in bug description for {bug['key']}")
        
        # Generate fixed HTML
        fixed_html = self.generator.generate_fixed_html(bug, html_content)
        if not fixed_html:
            return False
        
        self._save_fixed_file(bug['key'], fixed_html, github_url)
        return True
    
    def _save_fixed_file(self, bug_key: str, fixed_html: str, github_url: Optional[str] = None) -> None:
        """
        Save fixed HTML file
        """
        try:
            timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
            
            # Extract filename from GitHub URL
            filename = "index.html"
            if github_url and '/' in github_url:
                filename = github_url.split('/')[-1]
            
            # Create filename with bug key and timestamp
            base_name = filename.replace('.html', '')
            filename = os.path.join(self.fixed_dir, f'{base_name}_{bug_key}_{timestamp}.html')
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(fixed_html)
            
            logger.info(f"✅ Fixed HTML file saved: {filename}")
            
        except IOError as e:
            logger.error(f"Failed to save fixed file: {e}")


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
