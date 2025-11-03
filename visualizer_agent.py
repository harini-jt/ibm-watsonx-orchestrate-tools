"""
Visualizer Agent - Chart Generation Service
Generates interactive charts and dashboards for manufacturing data
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Pydantic models for chart requests

class TimeSeriesData(BaseModel):
    """Data for multi-line trend charts"""
    timestamps: List[str]
    series: List[Dict[str, Any]]  # [{"name": "Energy", "data": [...]}, ...]
    title: Optional[str] = "Time Series Chart"
    y_axis_label: Optional[str] = "Value"

class CategoryData(BaseModel):
    """Data for bar/pie charts"""
    categories: List[str]  # e.g., ["Zone-Paint", "Zone-Body", ...]
    series: List[Dict[str, Any]]  # [{"name": "Energy", "data": [100, 200, ...]}, ...]
    title: Optional[str] = "Category Chart"
    chart_type: str = "bar"  # "bar" or "pie"

class ScatterData(BaseModel):
    """Data for scatter plots"""
    x_values: List[float]
    y_values: List[float]
    labels: Optional[List[str]] = None
    title: Optional[str] = "Scatter Plot"
    x_label: Optional[str] = "X Axis"
    y_label: Optional[str] = "Y Axis"


# Chart generation functions

def generate_plotly_line_chart(data: TimeSeriesData) -> dict:
    """
    Generate Plotly JSON config for multi-line time series chart
    Perfect for: Energy trends, CO2 emissions over time, production metrics
    """
    traces = []
    
    for series in data.series:
        traces.append({
            "type": "scatter",
            "mode": "lines+markers",
            "name": series.get("name", "Series"),
            "x": data.timestamps,
            "y": series.get("data", []),
            "line": {"width": 2},
            "marker": {"size": 6}
        })
    
    layout = {
        "title": {"text": data.title, "font": {"size": 20}},
        "xaxis": {"title": "Time", "showgrid": True},
        "yaxis": {"title": data.y_axis_label, "showgrid": True},
        "hovermode": "x unified",
        "legend": {"orientation": "h", "y": -0.2},
        "template": "plotly_white"
    }
    
    return {
        "data": traces,
        "layout": layout,
        "config": {"responsive": True, "displayModeBar": True}
    }


def generate_plotly_bar_chart(data: CategoryData) -> dict:
    """
    Generate Plotly JSON config for grouped/stacked bar chart
    Perfect for: Zone comparisons, shift analysis, category breakdown
    """
    traces = []
    
    for series in data.series:
        traces.append({
            "type": "bar",
            "name": series.get("name", "Series"),
            "x": data.categories,
            "y": series.get("data", []),
            "text": series.get("data", []),
            "textposition": "auto"
        })
    
    layout = {
        "title": {"text": data.title, "font": {"size": 20}},
        "xaxis": {"title": "Category"},
        "yaxis": {"title": "Value"},
        "barmode": "group",  # or "stack"
        "template": "plotly_white",
        "showlegend": True
    }
    
    return {
        "data": traces,
        "layout": layout,
        "config": {"responsive": True}
    }


def generate_plotly_pie_chart(categories: List[str], values: List[float], title: str) -> dict:
    """
    Generate Plotly JSON config for pie chart
    Perfect for: Energy distribution by zone, shift breakdown, status proportions
    """
    trace = {
        "type": "pie",
        "labels": categories,
        "values": values,
        "textinfo": "label+percent",
        "textposition": "inside",
        "hoverinfo": "label+value+percent",
        "marker": {
            "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        }
    }
    
    layout = {
        "title": {"text": title, "font": {"size": 20}},
        "template": "plotly_white",
        "showlegend": True
    }
    
    return {
        "data": [trace],
        "layout": layout,
        "config": {"responsive": True}
    }


def generate_plotly_scatter(data: ScatterData) -> dict:
    """
    Generate Plotly JSON config for scatter plot
    Perfect for: Correlation analysis (energy vs production, efficiency vs emissions)
    """
    trace = {
        "type": "scatter",
        "mode": "markers",
        "x": data.x_values,
        "y": data.y_values,
        "text": data.labels if data.labels else None,
        "marker": {
            "size": 10,
            "color": data.y_values,
            "colorscale": "Viridis",
            "showscale": True
        }
    }
    
    layout = {
        "title": {"text": data.title, "font": {"size": 20}},
        "xaxis": {"title": data.x_label},
        "yaxis": {"title": data.y_label},
        "template": "plotly_white",
        "hovermode": "closest"
    }
    
    return {
        "data": [trace],
        "layout": layout,
        "config": {"responsive": True}
    }


def generate_anomaly_heatmap(zones: List[str], timestamps: List[str], anomaly_counts: List[List[int]]) -> dict:
    """
    Generate Plotly JSON config for anomaly heatmap
    Perfect for: Visualizing when and where anomalies occur
    """
    trace = {
        "type": "heatmap",
        "x": timestamps,
        "y": zones,
        "z": anomaly_counts,
        "colorscale": "Reds",
        "hovertemplate": "Zone: %{y}<br>Time: %{x}<br>Anomalies: %{z}<extra></extra>"
    }
    
    layout = {
        "title": {"text": "Anomaly Detection Heatmap", "font": {"size": 20}},
        "xaxis": {"title": "Time"},
        "yaxis": {"title": "Manufacturing Zone"},
        "template": "plotly_white"
    }
    
    return {
        "data": [trace],
        "layout": layout,
        "config": {"responsive": True}
    }


def generate_kpi_cards(kpis: dict) -> List[dict]:
    """
    Generate dashboard KPI card configs
    Perfect for: Summary metrics at the top of dashboards
    """
    cards = []
    
    # Energy KPI
    cards.append({
        "title": "Total Energy",
        "value": f"{kpis.get('total_energy_kwh', 0):,.0f} kWh",
        "trend": "up" if kpis.get('energy_trend', 0) > 0 else "down",
        "trend_value": f"{abs(kpis.get('energy_trend', 0)):.1f}%",
        "icon": "⚡",
        "color": "blue"
    })
    
    # CO2 KPI
    cards.append({
        "title": "CO₂ Emissions",
        "value": f"{kpis.get('total_co2_kg', 0):,.0f} kg",
        "trend": "down" if kpis.get('co2_trend', 0) < 0 else "up",
        "trend_value": f"{abs(kpis.get('co2_trend', 0)):.1f}%",
        "icon": "🌍",
        "color": "green"
    })
    
    # Production KPI
    cards.append({
        "title": "Production",
        "value": f"{kpis.get('total_vehicles', 0):,} units",
        "trend": "up" if kpis.get('production_trend', 0) > 0 else "down",
        "trend_value": f"{abs(kpis.get('production_trend', 0)):.1f}%",
        "icon": "🚗",
        "color": "purple"
    })
    
    # Efficiency KPI
    cards.append({
        "title": "Energy Efficiency",
        "value": f"{kpis.get('energy_per_vehicle_kwh', 0):.0f} kWh/unit",
        "trend": "down" if kpis.get('efficiency_trend', 0) < 0 else "up",
        "trend_value": f"{abs(kpis.get('efficiency_trend', 0)):.1f}%",
        "icon": "📊",
        "color": "orange"
    })
    
    return cards


def generate_dashboard_config(kpis: dict, trend_data: dict, zone_data: dict, anomaly_count: int) -> dict:
    """
    Generate complete dashboard configuration
    Perfect for: Full-page sustainability dashboard
    """
    return {
        "title": "Plant Sustainability Dashboard",
        "timestamp": datetime.now().isoformat(),
        "kpi_cards": generate_kpi_cards(kpis),
        "charts": [
            {
                "id": "energy-trend",
                "title": "Energy & CO₂ Trends",
                "type": "line",
                "width": "full",
                "config": generate_plotly_line_chart(TimeSeriesData(**trend_data))
            },
            {
                "id": "zone-comparison",
                "title": "Energy by Zone",
                "type": "bar",
                "width": "half",
                "config": generate_plotly_bar_chart(CategoryData(**zone_data))
            },
            {
                "id": "zone-distribution",
                "title": "Energy Distribution",
                "type": "pie",
                "width": "half",
                "config": generate_plotly_pie_chart(
                    categories=zone_data.get("categories", []),
                    values=[s["data"][0] for s in zone_data.get("series", [])],
                    title="Energy by Zone"
                )
            }
        ],
        "alerts": [
            {
                "type": "warning" if anomaly_count > 0 else "success",
                "message": f"{anomaly_count} anomalies detected" if anomaly_count > 0 else "No anomalies detected",
                "icon": "⚠️" if anomaly_count > 0 else "✅"
            }
        ]
    }
