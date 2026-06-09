#!/usr/bin/env python3
"""
Backend API Server for Bug Workflow
Provides REST API endpoints to trigger and monitor workflow
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from bug_workflow_claude import main as run_workflow
import threading
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow requests from dashboard

# Store execution history
execution_history = {
    'last_run': None,
    'last_status': 'idle',
    'bugs_processed': 0,
    'error_message': None
}

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current workflow status"""
    return jsonify({
        'status': execution_history['last_status'],
        'last_run': execution_history['last_run'],
        'bugs_processed': execution_history['bugs_processed'],
        'error': execution_history['error_message']
    })

@app.route('/api/trigger', methods=['POST'])
def trigger_workflow():
    """Manually trigger the workflow"""
    # Check if already running
    if execution_history['last_status'] == 'running':
        return jsonify({
            'status': 'error',
            'message': 'Workflow is already running'
        }), 409
    
    # Mark as running
    execution_history['last_status'] = 'running'
    execution_history['error_message'] = None
    
    # Run in background thread (don't block the API)
    thread = threading.Thread(target=run_workflow_async)
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': 'Workflow triggered',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get workflow execution logs"""
    try:
        log_file = os.path.join(os.getcwd(), 'logs', 'workflow.log')
        
        if not os.path.exists(log_file):
            return jsonify({
                'logs': ["[INFO] Waiting for workflow to start... No logs yet."]
            })
        
        # Read the file with proper encoding
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
            
            if not logs:
                return jsonify({
                    'logs': ["[INFO] Log file is empty. Waiting for workflow to run."]
                })
            
            # Return last 100 lines
            return jsonify({
                'logs': logs[-100:]
            })
            
    except Exception as e:
        print(f"Error reading logs: {str(e)}")
        return jsonify({
            'logs': [f"[ERROR] Error reading logs: {str(e)}"]
        })

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear workflow logs"""
    try:
        log_file = os.path.join(os.getcwd(), 'logs', 'workflow.log')
        if os.path.exists(log_file):
            open(log_file, 'w').close()
            return jsonify({
                'status': 'success',
                'message': 'Logs cleared'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/debug/paths', methods=['GET'])
def debug_paths():
    """Debug: Show current paths"""
    return jsonify({
        'working_directory': os.getcwd(),
        'logs_directory': os.path.join(os.getcwd(), 'logs'),
        'logs_file': os.path.join(os.getcwd(), 'logs', 'workflow.log'),
        'logs_exist': os.path.exists(os.path.join(os.getcwd(), 'logs')),
        'log_file_exists': os.path.exists(os.path.join(os.getcwd(), 'logs', 'workflow.log'))
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'api_version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration (non-sensitive)"""
    return jsonify({
        'jira_url': os.getenv('JIRA_API_URL'),
        'jira_project': os.getenv('JIRA_PROJECT_KEY'),
        'claude_model': os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
    })

# ============================================
# HELPER FUNCTIONS
# ============================================

def run_workflow_async():
    """Run workflow in background thread"""
    try:
        execution_history['last_run'] = datetime.now().isoformat()
        
        # Run the workflow
        result = run_workflow()
        
        # Update status
        execution_history['last_status'] = 'completed'
        execution_history['bugs_processed'] = result.get('bugs_processed', 0)
        execution_history['error_message'] = None
        
        print(f"✅ Workflow completed: {result}")
        
    except Exception as e:
        execution_history['last_status'] = 'error'
        execution_history['error_message'] = str(e)
        print(f"❌ Workflow error: {str(e)}")

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Print startup info
    print("🚀 Bug Workflow API Server Starting...")
    print(f"📍 Server: http://localhost:5000")
    print(f"📊 Dashboard: http://localhost:5000/dashboard.html")
    print(f"📋 API Docs:")
    print(f"   GET  /api/status    - Get workflow status")
    print(f"   POST /api/trigger   - Trigger workflow")
    print(f"   GET  /api/logs      - Get execution logs")
    print(f"   GET  /api/health    - Health check")
    print(f"   GET  /api/config    - Get configuration")
    print()
    print("⏸️  Press Ctrl+C to stop")
    print()
    
    # Start server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Important for threading
    )