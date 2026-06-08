#!/usr/bin/env python3
"""
Automated Bug Checking and Code Generation Workflow - OLLAMA VERSION
Uses local Ollama for free code generation (no API costs!)
"""

import os
import json
import logging
from datetime import datetime, timedelta
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


class OllamaCodeGenerator:
    """Client for generating code solutions using local Ollama"""
    
    def __init__(self, model: str = 'mistral'):
        self.model = model
        self.base_url = 'http://localhost:11434'
    
    def generate_solution(self, bug: Dict) -> Optional[str]:
        """
        Generate a code solution using local Ollama
        """
        try:
            prompt = self._build_prompt(bug)
            
            logger.info(f"Calling Ollama ({self.model}) for {bug['key']}...")
            
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'temperature': 0.7,
                },
                timeout=300   # Ollama can be slow
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error: {response.text}")
                return None
            
            result = response.json()
            solution = result.get('response', '')
            
            if solution:
                logger.info(f"Generated code solution for {bug['key']}")
                return solution
            else:
                logger.error(f"Empty response from Ollama for {bug['key']}")
                return None
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama. Is it running? (ollama serve)")
            return None
        except Exception as e:
            logger.error(f"Failed to generate code for {bug['key']}: {e}")
            return None
    
    @staticmethod
    def _build_prompt(bug: Dict) -> str:
        """Build the prompt for Ollama"""
        return f"""You are a senior software engineer. A bug has been reported:

Bug ID: {bug['key']}
Title: {bug['summary']}
Description: {bug['description']}
Priority: {bug['priority']}
Type: {bug.get('type', 'Unknown')}
Labels: {', '.join(bug['labels']) if bug['labels'] else 'None'}
Assigned to: {bug['assignee']}

Please provide a comprehensive solution including:

1. Root Cause Analysis: What's likely causing this bug?
2. Code Fix: Provide the exact code changes needed (in the appropriate language)
3. Test Cases: Write test cases to verify the fix
4. Deployment Notes: Any special considerations for deploying this fix
5. Prevention: How can we prevent similar bugs in the future?

Format your response using markdown with proper code blocks for code examples."""


class BugWorkflowOrchestrator:
    """Orchestrates the entire bug workflow"""
    
    def __init__(self):
        self.jira = JiraClient(
            base_url=os.getenv('JIRA_API_URL'),
            email=os.getenv('JIRA_EMAIL'),
            api_token=os.getenv('JIRA_API_TOKEN')
        )
        self.generator = OllamaCodeGenerator(
            model=os.getenv('OLLAMA_MODEL', 'mistral')
        )
        self.project_key = os.getenv('JIRA_PROJECT_KEY')
        self.solutions_dir = 'solutions'
        
        os.makedirs(self.solutions_dir, exist_ok=True)
    
    def run(self) -> Dict:
        """
        Run the complete workflow
        """
        logger.info("Starting bug workflow (using Ollama)...")
        
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
                time.sleep(1)
            
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
        
        solution = self.generator.generate_solution(bug)
        if not solution:
            return False
        
        self._save_solution(bug['key'], solution, bug)
        return True
    
    def _save_solution(self, bug_key: str, solution: str, bug: Dict) -> None:
        """
        Save generated solution to file
        """
        try:
            timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
            filename = os.path.join(self.solutions_dir, f'{bug_key}_{timestamp}.md')
            
            content = f"""# Bug Fix: {bug_key}

**Generated:** {datetime.now().isoformat()}
**Title:** {bug['summary']}
**Type:** {bug.get('type', 'Unknown')}
**Priority:** {bug['priority']}

## Solution

{solution}

---

*Generated by Automated Bug Workflow (using Ollama)*
"""
            
            with open(filename, 'w') as f:
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
        'JIRA_PROJECT_KEY'
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
