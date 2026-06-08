#!/usr/bin/env python3
"""
Automated Bug Checking and Code Generation Workflow
Reads HTML file from GitHub, analyzes bugs, generates specific code fixes
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
        """Extract plain text from Jira's rich text description"""
        if not description_obj:
            return ""
        
        try:
            content = description_obj.get('content', []) if isinstance(description_obj, dict) else []
            if content and isinstance(content[0], dict):
                text_content = content[0].get('content', [])
                if text_content and isinstance(text_content[0], dict):
                    return text_content[0].get('text', '')
        except (IndexError, KeyError, TypeError):
            pass
        
        return ""


class GitHubClient:
    """Client for fetching HTML files from GitHub"""
    
    @staticmethod
    def extract_github_url(description: str) -> Optional[str]:
        """
        Extract GitHub URL from bug description
        Looks for patterns like: https://github.com/...html or github.com URLs
        """
        # Pattern: https://github.com/user/repo/blob/branch/path/to/file.html
        pattern = r'(https?://(?:raw\.)?github\.com/[^\s]+\.html)'
        match = re.search(pattern, description)
        
        if match:
            url = match.group(1)
            # Convert regular GitHub URL to raw content URL
            if 'raw.github' not in url:
                url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
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
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully fetched HTML file ({len(response.text)} bytes)")
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
    
    def generate_solution(self, bug: Dict, html_content: Optional[str] = None) -> Optional[str]:
        """
        Generate a code solution for a bug
        If html_content is provided, uses it as context
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
                    'max_tokens': 2048,
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
            
            solution = response.json()['content'][0]['text']
            logger.info(f"Generated code solution for {bug['key']}")
            return solution
            
        except requests.RequestException as e:
            logger.error(f"Failed to generate code for {bug['key']}: {e}")
            return None
    
    @staticmethod
    def _build_prompt(bug: Dict, html_content: Optional[str] = None) -> str:
        """Build the prompt for Claude with HTML context if available"""
        
        if html_content:
            return f"""You are a senior web developer. A bug has been reported for an HTML file:

**Bug ID:** {bug['key']}
**Title:** {bug['summary']}
**Description:** {bug['description']}
**Priority:** {bug['priority']}
**Assigned to:** {bug['assignee']}

**HTML File to Fix:**
```html
{html_content}
```

Please analyze the HTML file and the bug description, then provide:

1. **Root Cause Analysis**: What in the HTML is causing this bug?
2. **Code Fix**: Provide the exact HTML/CSS/JavaScript changes needed with line numbers
3. **Changed Code**: Show the exact code blocks that need to be changed (in full, not snippets)
4. **Test Instructions**: How to verify the fix works
5. **Prevention**: How can we prevent similar bugs in the future?

Format your response using markdown with proper code blocks for code examples."""
        
        else:
            # Fallback if no HTML file found
            return f"""You are a senior software engineer. A bug has been reported:

**Bug ID:** {bug['key']}
**Title:** {bug['summary']}
**Description:** {bug['description']}
**Priority:** {bug['priority']}
**Type:** {bug.get('type', 'Unknown')}
**Assigned to:** {bug['assignee']}

Note: No HTML file was found in the bug description. 
Please analyze the bug description and provide what you can.

Please provide a comprehensive solution including:

1. **Root Cause Analysis**: What's likely causing this bug?
2. **Code Fix**: Provide the exact code changes needed
3. **Test Cases**: Write test cases to verify the fix
4. **Deployment Notes**: Any special considerations for deploying this fix
5. **Prevention**: How can we prevent similar bugs in the future?

Format your response using markdown with proper code blocks for code examples."""


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
        self.solutions_dir = 'solutions'
        
        os.makedirs(self.solutions_dir, exist_ok=True)
    
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
        
        if not self.jira.mark_in_progress(bug['key']):
            return False
        
        # Try to fetch HTML file from GitHub
        html_content = None
        github_url = GitHubClient.extract_github_url(bug['description'])
        if github_url:
            html_content = GitHubClient.fetch_html_file(github_url)
        
        if not github_url:
            logger.warning(f"No GitHub URL found in bug description for {bug['key']}")
        
        # Generate solution (with or without HTML context)
        solution = self.generator.generate_solution(bug, html_content)
        if not solution:
            return False
        
        self._save_solution(bug['key'], solution, bug, github_url)
        return True
    
    def _save_solution(self, bug_key: str, solution: str, bug: Dict, github_url: Optional[str] = None) -> None:
        """
        Save generated solution to file
        """
        try:
            timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
            filename = os.path.join(self.solutions_dir, f'{bug_key}_{timestamp}.md')
            
            github_section = f"\n**GitHub File:** {github_url}\n" if github_url else ""
            
            content = f"""# Bug Fix: {bug_key}

**Generated:** {datetime.now().isoformat()}
**Title:** {bug['summary']}
**Type:** {bug.get('type', 'Unknown')}
**Priority:** {bug['priority']}
**Assigned to:** {bug['assignee']}{github_section}

## Solution

{solution}

---

*Generated by Automated Bug Workflow*
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Solution saved to {filename}")
            
        except IOError as e:
            logger.error(f"Failed to save solution: {e}")


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