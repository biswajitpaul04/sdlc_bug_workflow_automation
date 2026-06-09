#!/usr/bin/env python3
"""
Automated Bug Checking and Code Generation Workflow
FIXED: Uses Jira Agile API (/rest/agile/1.0) instead of search API
This works with Scrum/Kanban boards when search is disabled
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

# Configure logging
log_file = os.path.join('logs', 'workflow.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Content-Type': 'application/json'})
        logger.info(f"JiraClient initialized with base URL: {self.base_url}")
    
    def get_agile_boards(self) -> List[Dict]:
        """Get all Agile boards"""
        try:
            logger.info("Fetching Agile boards...")
            url = f'{self.base_url}/rest/agile/1.0/board'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            boards = data.get('values', [])
            logger.info(f"Found {len(boards)} board(s)")
            
            for board in boards:
                logger.info(f"  - {board.get('name')} (ID: {board.get('id')}, Type: {board.get('type')})")
            
            return boards
        except Exception as e:
            logger.error(f"Failed to fetch Agile boards: {e}")
            return []
    
    def get_board_issues(self, board_id: int, status: str = "To Do") -> List[Dict]:
        """
        FIXED: Get issues from Agile board with specific status
        This works when /rest/api/3/search is disabled
        """
        try:
            logger.info(f"Fetching issues from board {board_id} with status '{status}'...")
            
            # Get all issues from the board
            url = f'{self.base_url}/rest/agile/1.0/board/{board_id}/issue'
            
            # JQL filter for status
            jql = f'status = "{status}"'
            params = {
                'jql': jql,
                'maxResults': 50,
                'fields': ['key', 'summary', 'description', 'assignee', 'priority', 'status']
            }
            
            logger.info(f"JQL: {jql}")
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 404:
                logger.warning("Board issue endpoint not available, trying alternative...")
                return self._get_issues_via_backlog(board_id, status)
            
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            logger.info(f"Found {len(issues)} issues with status '{status}'")
            
            bugs = []
            for issue in issues:
                try:
                    fields = issue.get('fields', {})
                    
                    bug = {
                        'key': issue.get('key', 'UNKNOWN'),
                        'summary': fields.get('summary', 'No summary'),
                        'description': self._extract_description(fields.get('description')),
                        'priority': fields.get('priority', {}).get('name', 'Medium') if fields.get('priority') else 'Medium',
                        'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                        'status': fields.get('status', {}).get('name', 'Unknown') if fields.get('status') else 'Unknown',
                    }
                    bugs.append(bug)
                    logger.info(f"✓ Parsed: {bug['key']}")
                except Exception as e:
                    logger.error(f"Error parsing issue: {e}")
                    continue
            
            return bugs
        
        except Exception as e:
            logger.error(f"Failed to fetch board issues: {e}")
            return []
    
    def _get_issues_via_backlog(self, board_id: int, status: str) -> List[Dict]:
        """Alternative: Get issues from board backlog"""
        try:
            logger.info("Trying backlog endpoint...")
            url = f'{self.base_url}/rest/agile/1.0/board/{board_id}/backlog'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            issues = data.get('issues', [])
            
            # Filter by status
            filtered_issues = [i for i in issues if i.get('fields', {}).get('status', {}).get('name') == status]
            logger.info(f"Found {len(filtered_issues)} issues with status '{status}'")
            
            bugs = []
            for issue in filtered_issues:
                try:
                    fields = issue.get('fields', {})
                    bug = {
                        'key': issue.get('key', 'UNKNOWN'),
                        'summary': fields.get('summary', 'No summary'),
                        'description': self._extract_description(fields.get('description')),
                        'priority': fields.get('priority', {}).get('name', 'Medium') if fields.get('priority') else 'Medium',
                        'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                        'status': fields.get('status', {}).get('name', 'Unknown') if fields.get('status') else 'Unknown',
                    }
                    bugs.append(bug)
                except Exception as e:
                    logger.error(f"Error parsing issue: {e}")
                    continue
            
            return bugs
        except Exception as e:
            logger.error(f"Failed to fetch backlog issues: {e}")
            return []
    
    def get_new_bugs(self, project_key: str) -> List[Dict]:
        """Get bugs using Agile API instead of search"""
        try:
            logger.info(f"Fetching bugs for project: {project_key}")
            
            # Step 1: Get boards
            boards = self.get_agile_boards()
            
            if not boards:
                logger.error("No Agile boards found!")
                return []
            
            # Step 2: Find board for this project
            project_board = None
            for board in boards:
                # Check if board is for this project
                if project_key.lower() in board.get('name', '').lower():
                    project_board = board
                    break
            
            if not project_board:
                # Use first board if project name not found
                logger.warning(f"Project board for {project_key} not found, using first board")
                project_board = boards[0]
            
            board_id = project_board.get('id')
            logger.info(f"Using board: {project_board.get('name')} (ID: {board_id})")
            
            # Step 3: Get issues from board with "To Do" status
            bugs = self.get_board_issues(board_id, status="To Do")
            
            logger.info(f"Successfully retrieved {len(bugs)} bugs")
            return bugs
        
        except Exception as e:
            logger.error(f"Failed to get new bugs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_available_transitions(self, issue_key: str) -> Dict:
        """Fetch available transitions for an issue"""
        try:
            logger.info(f"Fetching available transitions for {issue_key}...")
            url = f'{self.base_url}/rest/api/3/issue/{issue_key}/transitions'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            transitions = response.json().get('transitions', [])
            transition_dict = {t['name']: t['id'] for t in transitions}
            logger.info(f"Available transitions: {list(transition_dict.keys())}")
            return transition_dict
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch transitions for {issue_key}: {e}")
            return {}
    
    def mark_in_progress(self, issue_key: str, transition_id: Optional[str] = None) -> bool:
        """Mark a bug as In Progress"""
        response = None
        try:
            logger.info(f"Marking {issue_key} as In Progress...")
            
            if not transition_id:
                available = self.get_available_transitions(issue_key)
                
                if not available:
                    logger.error(f"❌ No transitions available for {issue_key}")
                    return False
                
                for name in ['In Progress', 'Start Progress', 'Start Work', 'To In Progress']:
                    if name in available:
                        transition_id = available[name]
                        logger.info(f"✓ Found transition '{name}' with ID: {transition_id}")
                        break
                
                if not transition_id:
                    logger.error(f"❌ Could not find 'In Progress' transition")
                    logger.error(f"Available: {list(available.keys())}")
                    return False
            
            url = f'{self.base_url}/rest/api/3/issue/{issue_key}/transitions'
            response = self.session.post(
                url,
                json={'transition': {'id': transition_id}},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"✓ Successfully marked {issue_key} as In Progress")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update {issue_key}: {e}")
            if response is not None:
                logger.error(f"HTTP Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
            return False
    
    @staticmethod
    def _extract_description(description_obj: Optional[Dict]) -> str:
        """Extract plain text from Jira description"""
        if not description_obj:
            return ""
        
        try:
            if isinstance(description_obj, str):
                return description_obj
            
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
                        elif 'content' in item:
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
        # Exclude whitespace, ), |, and other invalid URL chars
        pattern = r'(https?://(?:raw\.)?(?:github\.com|githubusercontent\.com)/[^\s\)\|\[\]\{\}]+\.html(?:\?[^\s\)\|\[\]\{\}]*)?)'
        match = re.search(pattern, description)
        
        if match:
            url = match.group(1)
            if 'github.com' in url and 'raw.' not in url:
                url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            url = url.replace('/refs/heads/', '/')
            
            # Clean up any remaining invalid characters
            url = url.rstrip('|[]{}')
            
            logger.info(f"Found GitHub URL: {url}")
            return url
        return None
    
    @staticmethod
    def fetch_html_file(url: str) -> Optional[str]:
        """Fetch HTML file from GitHub"""
        try:
            logger.info(f"Fetching HTML from GitHub...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logger.info(f"✓ Successfully fetched HTML ({len(response.text)} bytes)")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch HTML: {e}")
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
            logger.info(f"Calling Claude API for {bug['key']}...")
            
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
                    'messages': [{'role': 'user', 'content': prompt}]
                },
                timeout=120  # Increased from 30 to 120 seconds for slow API responses
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code}")
                return None
            
            response_text = response.json()['content'][0]['text']
            fixed_html = self._extract_html_from_response(response_text)
            
            if fixed_html:
                logger.info(f"✓ Generated fixed HTML for {bug['key']}")
                return fixed_html
            else:
                logger.error(f"Could not extract HTML from response")
                return None
        
        except Exception as e:
            logger.error(f"Failed to generate code: {e}")
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

Analyze the bug and provide the COMPLETE, FIXED HTML code. Return only the code wrapped in ```html``` tags."""
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
        logger.info("Starting bug workflow (using Agile API)...")
        logger.info("=" * 60)
        
        try:
            bugs = self.jira.get_new_bugs(self.project_key)
            
            if not bugs:
                logger.info("No bugs found with 'To Do' status.")
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
        """Process a single bug - only mark as In Progress if ALL steps succeed"""
        logger.info(f"Bug: {bug['key']} - {bug['summary']}")
        logger.info(f"Priority: {bug['priority']} | Status: {bug.get('status', 'Unknown')}")
        
        # Step 1: Extract GitHub URL
        logger.info("Step 1/3: Extracting GitHub URL...")
        html_content = None
        github_url = GitHubClient.extract_github_url(bug['description'])
        
        if github_url:
            logger.info("Step 2/3: Fetching HTML file...")
            html_content = GitHubClient.fetch_html_file(github_url)
            if not html_content:
                logger.warning(f"⚠ Could not fetch HTML, but continuing with bug description...")
        else:
            logger.warning(f"⚠ No GitHub URL found, using bug description only...")
        
        # Step 2: Generate fixed code
        logger.info("Step 3/3: Generating fixed code...")
        fixed_html = self.generator.generate_fixed_html(bug, html_content)
        
        if not fixed_html:
            logger.error(f"✗ Failed to generate code - NOT marking as In Progress")
            logger.error(f"✗ Bug {bug['key']} will remain in '{bug.get('status', 'Unknown')}' status")
            return False
        
        # Step 3: Only mark as In Progress if code generation succeeded
        logger.info("Step 4/3: Marking bug as In Progress...")
        if not self.jira.mark_in_progress(bug['key']):
            logger.warning(f"⚠ Could not mark as In Progress, but code was generated")
        
        # Step 4: Save the fixed file
        self._save_fixed_file(bug['key'], fixed_html, bug['summary'])
        logger.info(f"✓ Completed: {bug['key']}")
        return True
    
    def _save_fixed_file(self, bug_key: str, fixed_html: str, bug_summary: str) -> None:
        """Save fixed file"""
        try:
            safe_summary = bug_summary.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = os.path.join(self.fixed_dir, f'{bug_key}_{safe_summary}.html')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(fixed_html)
            logger.info(f"✓ File saved: {filename}")
        except IOError as e:
            logger.error(f"Failed to save file: {e}")


def main():
    """Main entry point"""
    required_vars = ['JIRA_API_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY', 'CLAUDE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing: {', '.join(missing)}")
        return {'status': 'failed', 'error': 'Missing config'}
    
    orchestrator = BugWorkflowOrchestrator()
    return orchestrator.run()


if __name__ == '__main__':
    result = main()
    exit(0 if result['status'] == 'completed' else 1)
