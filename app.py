from flask import Flask, render_template_string, request, jsonify
import logging
import os
from dotenv import load_dotenv
from openproject_client import OpenProjectClient
from gantt_chart_generator import GanttChartGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

OPENPROJECT_URL = os.getenv('OPENPROJECT_URL')
OPENPROJECT_API_KEY = os.getenv('OPENPROJECT_API_KEY')

if not OPENPROJECT_URL or not OPENPROJECT_API_KEY:
    logger.error("Please set OPENPROJECT_URL and OPENPROJECT_API_KEY environment variables")
    exit(1)

op_client = OpenProjectClient(OPENPROJECT_URL, OPENPROJECT_API_KEY)
gantt_generator = GanttChartGenerator(op_client)

# Load HTML template from file
with open('templates/main_template.html') as f:
    HTML_TEMPLATE = f.read()

@app.route('/')
def index():
    try:
        projects = op_client.get_projects()
        logger.info(f"Successfully retrieved {len(projects)} projects")
        return render_template_string(HTML_TEMPLATE, projects=projects, error=None)
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        error_msg = str(e)
        if "Authentication failed" in error_msg or "401" in error_msg:
            error_msg = "Authentication failed. Please check your OPENPROJECT_API_KEY environment variable."
        elif "403" in error_msg:
            error_msg = "Access forbidden. Your API key doesn't have sufficient permissions to view projects."
        elif "Connection" in error_msg:
            error_msg = f"Cannot connect to OpenProject at {OPENPROJECT_URL}. Please check your OPENPROJECT_URL environment variable."
        return render_template_string(HTML_TEMPLATE, projects=[], error=error_msg)

@app.route('/gantt/<int:project_id>')
def gantt_chart(project_id: int):
    return gantt_generator.generate_gantt_chart(project_id)

@app.route('/gantt_epic/<int:project_id>')
def gantt_chart_epic(project_id: int):
    return gantt_generator.generate_gantt_chart(project_id, epic_only=True)

# ...existing code for other routes...

if __name__ == '__main__':
    print(f"Starting OpenProject Gantt Chart Generator")
    print(f"OpenProject URL: {OPENPROJECT_URL}")
    print(f"API Key configured: {'Yes' if OPENPROJECT_API_KEY else 'No'}")
    if not OPENPROJECT_URL or not OPENPROJECT_API_KEY:
        print("\n❌ ERROR: Missing required environment variables!")
        print("Please create a .env file with:")
        print("OPENPROJECT_URL=https://your-openproject-instance.com")
        print("OPENPROJECT_API_KEY=your_api_key_here")
        exit(1)
    print(f"Server will be available at: http://localhost:5000")
    print(f"Test authentication at: http://localhost:5000/test-auth")
    app.run(debug=True, host='0.0.0.0', port=5000)
