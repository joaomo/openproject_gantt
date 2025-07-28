import logging
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

class GanttChartGenerator:
    """Generate Gantt charts from OpenProject data"""
    def __init__(self, openproject_client):
        self.client = openproject_client

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _get_status_color(self, status, start, finish, now, closed_statuses=None):
        if closed_statuses is None:
            closed_statuses = {'Closed', 'closed', 'CLOSED'}
        if status in closed_statuses:
            return '#27ae60'
        if start and now and start > now:
            return '#9b59b6'
        if start and finish and now and start <= now <= finish:
            return '#3498db'
        if finish and now and finish < now:
            return '#e74c3c'
        return '#95a5a6'

    def _extract_work_package_data(self, work_packages):
        data = []
        now = datetime.utcnow()
        def wrap_name(name, max_chars=100, max_lines=2):
            if len(name) <= max_chars:
                return name
            words = name.split()
            lines = []
            current_line = ''
            for word in words:
                if len(current_line) + len(word) + 1 <= max_chars:
                    if current_line:
                        current_line += ' '
                    current_line += word
                else:
                    lines.append(current_line)
                    current_line = word
                    if len(lines) == max_lines - 1:
                        break
            if current_line:
                lines.append(current_line)
            if len(lines) > max_lines:
                lines = lines[:max_lines]
            result = '<br>'.join(lines)
            if len(lines) == max_lines and (len(current_line) + sum(len(l) for l in lines[:-1])) < len(name):
                result += '...'
            return result

        for wp in work_packages:
            wp_id = wp.get('id')
            subject = wp.get('subject', 'Untitled')
            wrapped_subject = wrap_name(subject)
            start_date = self._parse_date(wp.get('startDate') or wp.get('derivedStartDate'))
            due_date = self._parse_date(wp.get('dueDate') or wp.get('derivedDueDate'))
            if start_date and not due_date:
                due_date = start_date + timedelta(days=1)
            elif due_date and not start_date:
                start_date = due_date - timedelta(days=1)
            status = wp.get('_links', {}).get('status', {}).get('title', 'Unknown')
            progress = wp.get('percentageDone', 0) / 100.0 if wp.get('percentageDone') is not None else 0
            assignee = wp.get('_links', {}).get('assignee', {}).get('title', 'Unassigned')
            type_name = wp.get('_links', {}).get('type', {}).get('title', 'Task')
            color = self._get_status_color(status, start_date, due_date, now)
            missing_start = start_date is None
            data.append({
                'id': wp_id,
                'Task': f"#{wp_id}: {wrapped_subject}",
                'Start': start_date,
                'Finish': due_date,
                'Status': status,
                'Progress': progress,
                'Assignee': assignee,
                'Type': type_name,
                'Color': color,
                'Duration': (due_date - start_date).days if start_date and due_date else 0,
                'MissingStart': missing_start
            })
        return pd.DataFrame(data)

    def generate_gantt_chart(self, project_id, epic_only=False):
        try:
            # Get project information
            project = self.client.get_project(project_id)
            project_name = project.get('name', f'Project {project_id}')

            # Get work packages
            work_packages = self.client.get_work_packages(project_id)
            logging.info(f"Found {len(work_packages)} work packages for project {project_id}")

            if not work_packages:
                return f"<div class='alert alert-info'><h4>No Work Packages Found</h4><p>Project '{project_name}' has no work packages to display in the Gantt chart.</p></div>"

            # Convert to DataFrame
            df = self._extract_work_package_data(work_packages)
            logging.info(f"Processed {len(df)} work packages with dates")

            if epic_only:
                df = df[df['Type'].str.lower() == 'epic']
                logging.info(f"Filtered to {len(df)} EPIC work packages")

            if df.empty:
                return f"<div class='alert alert-warning'><h4>No Scheduled Tasks</h4><p>Project '{project_name}' has work packages, but none have start or due dates set.</p><p>Please set dates for work packages to display them in the Gantt chart.</p></div>"
            # Sort by start date, but put tasks with missing start at the end
            if 'MissingStart' in df.columns:
                df = df.sort_values(['MissingStart', 'Start'], ascending=[True, True])
            else:
                df = df.sort_values('Start')

            # --- Project-relative weeks logic (robust) ---
            if not df.empty:
                valid_starts = df['Start'].dropna()
                if not valid_starts.empty:
                    min_start = valid_starts.min()
                    def week_or_none(date):
                        if pd.notnull(date):
                            w = ((date - min_start).days // 7 + 1)
                            return w if w >= 1 else 1
                        return None
                    df['StartWeek'] = df['Start'].apply(week_or_none)
                    df['FinishWeek'] = df['Finish'].apply(week_or_none)
                    df.loc[df['FinishWeek'] == df['StartWeek'], 'FinishWeek'] = df['StartWeek'] + 1
                else:
                    df['StartWeek'] = None
                    df['FinishWeek'] = None

            df_plot = df[df['StartWeek'].notnull() & df['FinishWeek'].notnull()].copy()
            if df_plot.empty:
                logging.warning("No tasks with valid week values to plot.")
                return f"<div class='alert alert-warning'><h4>No Scheduled Tasks</h4><p>Project '{project_name}' has work packages, but none have start or due dates set.</p><p>Please set dates for work packages to display them in the Gantt chart.</p></div>"

            logging.info("Gantt DataFrame after week calculation:\n" + df_plot[['Task','Start','Finish','StartWeek','FinishWeek','Color']].to_string())

            fig = go.Figure()
            hovertemplate = (
                "<b>%{y}</b><br>"
                "Start: %{customdata[4]|%Y-%m-%d} (Week %{base})<br>"
                "End: %{customdata[5]|%Y-%m-%d} (Week %{x})<br>"
                "Status: %{customdata[6]}<br>"
                "Duration: %{customdata[0]} days<br>"
                "Progress: %{customdata[1]:.0%}<br>"
                "Assignee: %{customdata[2]}<br>"
                "Type: %{customdata[3]}<br>"
                "<extra></extra>"
            )
            for idx, row in df_plot.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['FinishWeek'] - row['StartWeek']],
                    y=[row['Task']],
                    base=row['StartWeek'],
                    orientation='h',
                    marker=dict(color=row['Color']),
                    customdata=[[row['Duration'], row['Progress'], row['Assignee'], row['Type'], row['Start'], row['Finish'], row['Status']]],
                    hovertemplate=hovertemplate,
                    name=row['Task'],
                    showlegend=False
                ))

            missing_start_df = df[df['MissingStart'] == True]
            y_labels = df_plot['Task'].tolist()[::-1]
            for i, (_, row) in enumerate(missing_start_df.iterrows()):
                y_labels.insert(0, row['Task'])
                fig.add_annotation(
                    xref='paper', yref='y',
                    x=0.5, y=row['Task'],
                    text=f"{row['Task']} (No start date)",
                    showarrow=False,
                    font=dict(color='gray', size=12),
                    align='left',
                    bgcolor='#f8f9fa',
                    bordercolor='#ccc',
                    borderwidth=1,
                    opacity=0.8
                )

            max_week = int(df_plot['FinishWeek'].max()) if not df_plot.empty and df_plot['FinishWeek'].notnull().any() else 1
            week_ticks = list(range(1, max_week + 2))
            fig.update_layout(
                height=max(600, (len(df_plot) + len(missing_start_df)) * 40 + 150),
                margin=dict(l=20, r=20, t=80, b=50),
                xaxis_title="Project Week",
                yaxis_title="Tasks",
                showlegend=False,
                xaxis=dict(
                    tickmode='array',
                    tickvals=week_ticks,
                    ticktext=[f"Week {w}" for w in week_ticks],
                    range=[0.5, max_week + 1.5],
                    showgrid=True
                ),
                yaxis=dict(
                    showgrid=True,
                    categoryorder='array',
                    categoryarray=y_labels,
                ),
                hovermode='closest',
                barmode='stack'
            )
            html_content = fig.to_html(
                include_plotlyjs=True,
                div_id="gantt-chart",
                config={
                    'displayModeBar': True,
                    'responsive': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d']
                }
            )
            wrapped_html = f"""
            <div class="gantt-chart-container">
                <div class="chart-info mb-3">
                    <div class="row">
                        <div class="col-md-4">
                            <strong>Total Tasks:</strong> {len(df)}
                        </div>
                        <div class="col-md-4">
                            <strong>Week Range:</strong> Week {df['StartWeek'].min()} to Week {df['FinishWeek'].max()}
                        </div>
                        <div class="col-md-4">
                            <strong>Project Duration:</strong> {(df['Finish'].max() - df['Start'].min()).days} days
                        </div>
                    </div>
                </div>
                {html_content}
            </div>
            <style>
                .gantt-chart-container {{ width: 100%; height: auto; }}
                .chart-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                #gantt-chart {{ width: 100% !important; height: auto !important; }}
            </style>
            """
            return wrapped_html
        except Exception as e:
            logging.error(f"Error generating Gantt chart: {e}")
            import traceback
            traceback.print_exc()
            return f"<div class='alert alert-danger'><h4>Error generating Gantt chart</h4><p><strong>Error:</strong> {str(e)}</p><p>Please check the server logs for more details.</p></div>"
