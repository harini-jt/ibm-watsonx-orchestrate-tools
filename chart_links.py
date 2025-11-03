"""
Helper functions to convert Plotly charts to shareable links
"""

import json
import urllib.parse
import base64

def plotly_to_quickchart_url(plotly_config: dict) -> str:
    """
    Convert Plotly config to QuickChart.io URL (free service)
    Returns a URL that generates a chart image
    """
    # Extract data for Chart.js format (QuickChart uses Chart.js)
    chart_data = plotly_config.get('data', [])
    
    # Convert to Chart.js format
    if chart_data and chart_data[0].get('type') == 'scatter':
        # Line chart
        chart_config = {
            "type": "line",
            "data": {
                "labels": chart_data[0].get('x', []),
                "datasets": [
                    {
                        "label": trace.get('name', 'Series'),
                        "data": trace.get('y', []),
                        "fill": False,
                        "borderColor": f"rgb({i*50}, {100+i*30}, {200-i*20})"
                    }
                    for i, trace in enumerate(chart_data)
                ]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": plotly_config.get('layout', {}).get('title', {}).get('text', 'Chart')
                }
            }
        }
    elif chart_data and chart_data[0].get('type') == 'bar':
        # Bar chart
        chart_config = {
            "type": "bar",
            "data": {
                "labels": chart_data[0].get('x', []),
                "datasets": [
                    {
                        "label": trace.get('name', 'Series'),
                        "data": trace.get('y', [])
                    }
                    for trace in chart_data
                ]
            }
        }
    elif chart_data and chart_data[0].get('type') == 'pie':
        # Pie chart
        chart_config = {
            "type": "pie",
            "data": {
                "labels": chart_data[0].get('labels', []),
                "datasets": [{
                    "data": chart_data[0].get('values', [])
                }]
            }
        }
    else:
        # Default
        chart_config = {"type": "line", "data": {}}
    
    # Encode config
    config_json = json.dumps(chart_config)
    encoded = urllib.parse.quote(config_json)
    
    # Return QuickChart URL
    return f"https://quickchart.io/chart?c={encoded}&width=800&height=400"


def plotly_to_plotly_chart_studio(plotly_config: dict) -> str:
    """
    Alternative: Create a Plotly Chart Studio link
    (Requires Plotly account for persistent storage)
    """
    # For demo purposes, return a placeholder
    # In production, you'd upload to Plotly Chart Studio via API
    return "https://chart-studio.plotly.com/~your-username/chart-id"


def generate_inline_html_base64(plotly_config: dict) -> str:
    """
    Generate a base64-encoded HTML page with embedded chart
    Can be opened in browser via data: URL
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    </head>
    <body>
        <div id="chart" style="width:100%;height:600px;"></div>
        <script>
            var config = {json.dumps(plotly_config)};
            Plotly.newPlot('chart', config.data, config.layout, config.config);
        </script>
    </body>
    </html>
    """
    
    # Base64 encode
    html_bytes = html.encode('utf-8')
    base64_html = base64.b64encode(html_bytes).decode('utf-8')
    
    return f"data:text/html;base64,{base64_html}"
