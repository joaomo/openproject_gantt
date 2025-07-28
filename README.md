# OpenProject Gantt Chart Generator

A Python Flask web server that connects to OpenProject API and generates interactive Gantt charts for projects using Plotly.

## Features

- **Interactive Gantt Charts**: Generate beautiful, interactive Gantt charts using Plotly
- **Project Selection**: Browse and select from available OpenProject projects
- **Work Package Details**: View task details, assignees, status, progress, and timelines
- **Status-based Coloring**: Tasks are colored based on their status (New, In Progress, Resolved, etc.)
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile devices
- **API Endpoints**: Both web interface and JSON API endpoints available

## Requirements

Create a `requirements.txt` file:

```txt
Flask==2.3.3
requests==2.31.0
plotly==5.17.0
pandas==2.1.1
python-dotenv==1.0.0
Werkzeug==2.3.7
```

## Installation

1. **Clone or download the script**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment configuration**:
   Create a `.env` file in the same directory with your OpenProject credentials:
   ```env
   OPENPROJECT_URL=https://your-openproject-instance.com
   OPENPROJECT_API_KEY=your_api_key_here
   ```

## OpenProject API Key Setup

1. **Log into your OpenProject instance**
2. **Go to My Account → Access Tokens**
3. **Create a new API token**:
   - Give it a descriptive name (e.g., "Gantt Chart Generator")
   - Set appropriate permissions (at minimum: "View projects" and "View work packages")
4. **Copy the generated token** and use it as `OPENPROJECT_API_KEY`

### API Key Format

The application automatically handles the authentication format. OpenProject uses HTTP Basic Authentication where:
- **Username**: `apikey` (literal string)
- **Password**: Your API token
- **Format**: The application automatically base64-encodes `apikey:your_token`

**Important**: Use only the raw API token in your `.env` file - the application handles the encoding automatically.

Example `.env` file:
```env
OPENPROJECT_URL=https://your-openproject-instance.com
OPENPROJECT_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

## Usage

1. **Start the server**:
   ```bash
   python openproject_gantt_server.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Select a project** from the list to generate its Gantt chart

## API Endpoints

The server provides several API endpoints:

### Web Interface
- `GET /` - Main page with project selection
- `GET /gantt/<project_id>` - Generate Gantt chart HTML for a project

### JSON API
- `GET /api/projects` - Get all projects as JSON
- `GET /api/gantt/<project_id>` - Get Gantt chart data as JSON
- `GET /health` - Health check endpoint

### Example API Usage

```bash
# Get all projects
curl http://localhost:5000/api/projects

# Get Gantt data for project ID 1
curl http://localhost:5000/api/gantt/1

# Health check
curl http://localhost:5000/health
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENPROJECT_URL` | Your OpenProject instance URL | Yes |
| `OPENPROJECT_API_KEY` | OpenProject API token | Yes |

### Customization

You can customize the following aspects:

1. **Colors**: Modify the `_get_status_color()` method to change status-based colors
2. **Chart Layout**: Adjust the Plotly figure layout in `generate_gantt_chart()`
3. **Data Fields**: Add more work package fields in `_extract_work_package_data()`
4. **UI Theme**: Modify the Bootstrap classes in the HTML template

## Features Explained

### Work Package Processing

The system processes OpenProject work packages and:
- Extracts start and due dates (using derived dates if direct dates aren't available)
- Calculates task duration
- Determines status-based colors
- Handles missing dates by creating 1-day tasks or skipping tasks without dates

### Chart Generation

- **Interactive**: Hover over tasks to see detailed information
- **Responsive**: Charts automatically resize based on the number of tasks
- **Sorted**: Tasks are sorted by start date for logical viewing
- **Informative**: Shows task ID, subject, dates, duration, status, progress, assignee, and type

### Error Handling

The application includes comprehensive error handling:
- Connection issues with OpenProject
- Missing or invalid work packages
- Projects without scheduled tasks
- API authentication problems

## Testing Your Setup

After configuration, test your connection:

1. **Start the server**:
   ```bash
   python openproject_gantt_server.py
   ```

2. **Test authentication**:
   Visit `http://localhost:5000/test-auth` to verify your API connection

3. **Check startup logs** for connection status

## Troubleshooting

### Common Issues

1. **Authentication Error (401)**:
   - Verify your `OPENPROJECT_API_KEY` is correct
   - Ensure you copied the complete API token without extra spaces
   - The application automatically formats the authentication - use only the raw token

2. **Access Forbidden (403)**:
   - Ensure the API key has sufficient permissions:
     - View projects
     - View work packages
     - Access to the specific projects you want to chart

3. **Connection Issues**:
   - Verify `OPENPROJECT_URL` is correct and accessible
   - Ensure the URL includes `https://` or `http://`
   - Check firewall settings if using a private instance
   - Test the URL in your browser first

4. **Template Rendering Errors**:
   - Usually fixed in the latest version
   - Check server logs for specific error details

5. **Empty Gantt Charts**:
   - Ensure work packages have start and/or due dates set
   - Check that work packages exist in the selected project
   - Use the debug endpoint: `/debug/project/<project_id>`

### Debug Mode

The server runs in debug mode by default, showing detailed error messages. For production use, set `debug=False` in the `app.run()` call.

## Extending the Application

### Adding New Features

1. **Filtering**: Add filters for work package status, assignee, or type
2. **Export**: Add export functionality for charts (PNG, PDF, SVG)
3. **Real-time Updates**: Implement WebSocket connections for live updates
4. **Multiple Projects**: Display Gantt charts for multiple projects simultaneously
5. **Critical Path**: Highlight critical path based on work package dependencies

### Integration Options

- **Embed in OpenProject**: Use as a plugin or custom field
- **Standalone Dashboard**: Deploy as a monitoring dashboard
- **API Integration**: Use the JSON endpoints in other applications
- **Scheduled Reports**: Generate charts automatically and send via email

## License

This code is provided as-is for educational and practical use. Modify as needed for your requirements.