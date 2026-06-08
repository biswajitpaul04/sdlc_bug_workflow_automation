import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CLAUDE_API_KEY')
model = 'claude-3-5-sonnet-20241022'

print(f"Testing Claude API...")
print(f"API Key: {api_key[:20]}..." if api_key else "MISSING")
print(f"Model: {model}")
print()

response = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    },
    json={
        'model': model,
        'max_tokens': 100,
        'messages': [
            {
                'role': 'user',
                'content': 'Say hello'
            }
        ]
    }
)

print(f"Status: {response.status_code}")
print(f"Response:")
print(response.text)