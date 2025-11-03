"""
Action Agent (Remedy Agent) - Automated Remediation System
Analyzes anomalies and creates actionable remediation plans with Slack notifications
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

# Anomaly type configurations
ANOMALY_CONFIGS = {
    "PAINT_OVEN_IDLE": {
        "category": "Equipment Misuse",
        "typical_fix_time": "15 minutes",
        "typical_cost": "$0 (timer adjustment)",
        "severity_multiplier": 1.5,
        "root_causes": [
            "Timer malfunction",
            "Manual override not disabled",
            "Scheduling gap miscommunication"
        ],
        "fix_steps": [
            "Inspect paint oven timer settings",
            "Verify auto-shutdown during production gaps",
            "Test timer with production schedule",
            "Document timer configuration in maintenance log"
        ],
        "responsible_team": "Maintenance Team"
    },
    "COMPRESSED_AIR_LEAK": {
        "category": "Equipment Failure",
        "typical_fix_time": "30-45 minutes",
        "typical_cost": "$50-150 (seal/valve replacement)",
        "severity_multiplier": 1.2,
        "root_causes": [
            "Worn seal or gasket",
            "Loose connection",
            "Valve malfunction",
            "Pipe crack or damage"
        ],
        "fix_steps": [
            "Locate leak using ultrasonic detector",
            "Isolate affected zone/equipment",
            "Replace damaged seals or valves",
            "Pressure test after repair",
            "Monitor for 24 hours post-fix"
        ],
        "responsible_team": "Maintenance Team"
    },
    "HVAC_INEFFICIENCY": {
        "category": "Climate Control",
        "typical_fix_time": "20 minutes",
        "typical_cost": "$0 (setting adjustment)",
        "severity_multiplier": 0.8,
        "root_causes": [
            "Incorrect temperature setpoint",
            "Zone overcooling/overheating",
            "Sensor calibration drift",
            "Insulation gaps"
        ],
        "fix_steps": [
            "Review and adjust temperature setpoints",
            "Verify zone sensors are calibrated",
            "Check for air leaks or insulation gaps",
            "Optimize HVAC schedule with production hours"
        ],
        "responsible_team": "Facilities Team"
    },
    "STANDBY_POWER_EXCESSIVE": {
        "category": "Energy Waste",
        "typical_fix_time": "10 minutes",
        "typical_cost": "$0 (shutdown procedure)",
        "severity_multiplier": 1.0,
        "root_causes": [
            "Equipment left running during breaks",
            "No automated shutdown",
            "Operator oversight",
            "Missing shutdown procedure"
        ],
        "fix_steps": [
            "Identify equipment running in standby",
            "Create/update shutdown checklist",
            "Train operators on shutdown procedures",
            "Implement automated shutdown timers"
        ],
        "responsible_team": "Operations Team"
    },
    "PRODUCTION_EFFICIENCY_DROP": {
        "category": "Process Optimization",
        "typical_fix_time": "Variable (investigation required)",
        "typical_cost": "Variable",
        "severity_multiplier": 1.3,
        "root_causes": [
            "Machine calibration drift",
            "Material quality issues",
            "Operator training gap",
            "Maintenance backlog"
        ],
        "fix_steps": [
            "Analyze production data for patterns",
            "Inspect machine settings and calibration",
            "Review material batch quality",
            "Schedule preventive maintenance",
            "Provide operator training if needed"
        ],
        "responsible_team": "Production & Maintenance Teams"
    }
}

# Work order counter (in production, use database)
WORK_ORDER_COUNTER = 1000


def generate_work_order_id() -> str:
    """Generate unique work order ID"""
    global WORK_ORDER_COUNTER
    WORK_ORDER_COUNTER += 1
    date_str = datetime.now().strftime("%Y%m%d")
    return f"WO-{date_str}-{WORK_ORDER_COUNTER:04d}"


def calculate_priority_score(
    energy_waste_kwh: float,
    cost_per_day: float,
    severity: str,
    anomaly_type: str
) -> Dict[str, Any]:
    """
    Calculate priority score and classification
    Returns: {"score": int, "priority": str, "urgency": str}
    """
    # Base score from severity
    severity_scores = {"HIGH": 80, "MEDIUM": 50, "LOW": 20}
    base_score = severity_scores.get(severity, 50)
    
    # Financial impact multiplier
    if cost_per_day > 50:
        base_score += 20
    elif cost_per_day > 20:
        base_score += 10
    
    # Anomaly type multiplier
    config = ANOMALY_CONFIGS.get(anomaly_type, {})
    multiplier = config.get("severity_multiplier", 1.0)
    final_score = int(base_score * multiplier)
    
    # Classify priority
    if final_score >= 80:
        priority = "CRITICAL"
        urgency = "Immediate action required (within 2 hours)"
    elif final_score >= 60:
        priority = "HIGH"
        urgency = "Action required within 24 hours"
    elif final_score >= 40:
        priority = "MEDIUM"
        urgency = "Schedule within 3 days"
    else:
        priority = "LOW"
        urgency = "Address during next maintenance window"
    
    return {
        "score": final_score,
        "priority": priority,
        "urgency": urgency
    }


def calculate_financial_impact(
    energy_waste_kwh: float,
    duration_hours: float = 1.0,
    cost_per_kwh: float = 0.07
) -> Dict[str, Any]:
    """
    Calculate financial impact of anomaly
    Returns cost per hour, day, month, year, and potential savings
    """
    cost_per_hour = energy_waste_kwh * cost_per_kwh
    cost_per_day = cost_per_hour * 24
    cost_per_month = cost_per_day * 30
    cost_per_year = cost_per_day * 365
    
    return {
        "energy_waste_kwh_per_hour": round(energy_waste_kwh, 2),
        "cost_per_hour": round(cost_per_hour, 2),
        "cost_per_day": round(cost_per_day, 2),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2),
        "potential_annual_savings": round(cost_per_year, 2)
    }


def generate_remediation_plan(anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate complete remediation plan for an anomaly
    """
    # Extract anomaly details
    anomaly_type = anomaly_data.get("type", "UNKNOWN")
    zone = anomaly_data.get("zone", "Unknown Zone")
    energy_waste = anomaly_data.get("energy_waste_kwh", 0)
    severity = anomaly_data.get("severity", "MEDIUM")
    timestamp = anomaly_data.get("timestamp", datetime.now().isoformat())
    note = anomaly_data.get("note", "")
    
    # Get anomaly configuration
    config = ANOMALY_CONFIGS.get(anomaly_type, {
        "category": "Unknown",
        "typical_fix_time": "To be determined",
        "typical_cost": "To be estimated",
        "severity_multiplier": 1.0,
        "root_causes": ["Investigation required"],
        "fix_steps": ["Analyze anomaly", "Determine root cause", "Implement fix"],
        "responsible_team": "Maintenance Team"
    })
    
    # Calculate financial impact
    financial_impact = calculate_financial_impact(energy_waste)
    
    # Calculate priority
    priority_info = calculate_priority_score(
        energy_waste,
        financial_impact["cost_per_day"],
        severity,
        anomaly_type
    )
    
    # Generate work order
    work_order_id = generate_work_order_id()
    
    # Estimate fix completion time
    deadline = datetime.now() + timedelta(hours=2 if priority_info["priority"] == "CRITICAL" else 24)
    
    # Build remediation plan
    plan = {
        "work_order_id": work_order_id,
        "created_at": datetime.now().isoformat(),
        "status": "OPEN",
        "anomaly_details": {
            "type": anomaly_type,
            "category": config["category"],
            "zone": zone,
            "severity": severity,
            "detected_at": timestamp,
            "description": note or f"{anomaly_type.replace('_', ' ').title()} detected in {zone}"
        },
        "priority": {
            "level": priority_info["priority"],
            "score": priority_info["score"],
            "urgency": priority_info["urgency"],
            "deadline": deadline.isoformat()
        },
        "financial_impact": financial_impact,
        "root_cause_analysis": {
            "likely_causes": config["root_causes"],
            "investigation_required": anomaly_type == "UNKNOWN"
        },
        "remediation_steps": [
            {
                "step": i + 1,
                "action": step,
                "status": "PENDING",
                "responsible": config["responsible_team"]
            }
            for i, step in enumerate(config["fix_steps"])
        ],
        "resource_estimates": {
            "estimated_time": config["typical_fix_time"],
            "estimated_cost": config["typical_cost"],
            "responsible_team": config["responsible_team"],
            "required_skills": ["Equipment diagnosis", "Repair/adjustment"]
        },
        "expected_outcome": {
            "energy_savings_kwh_year": round(energy_waste * 24 * 365, 2),
            "cost_savings_year": financial_impact["potential_annual_savings"],
            "payback_period": "Immediate" if config["typical_cost"] == "$0 (timer adjustment)" else "< 1 month",
            "roi_percent": "∞" if "$0" in config["typical_cost"] else "500%+"
        }
    }
    
    return plan


def format_slack_message(remediation_plan: Dict[str, Any]) -> str:
    """
    Format remediation plan as a Slack message with rich formatting
    """
    anomaly = remediation_plan["anomaly_details"]
    priority = remediation_plan["priority"]
    financial = remediation_plan["financial_impact"]
    steps = remediation_plan["remediation_steps"]
    outcome = remediation_plan["expected_outcome"]
    
    # Priority emoji
    priority_emoji = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "⚡",
        "LOW": "ℹ️"
    }
    emoji = priority_emoji.get(priority["level"], "📋")
    
    # Build message
    message = f"""{emoji} *{priority['level']} PRIORITY ALERT*

*Anomaly Detected:* {anomaly['type'].replace('_', ' ').title()}
*Zone:* {anomaly['zone']}
*Category:* {anomaly['category']}
*Detected:* {datetime.fromisoformat(anomaly['detected_at']).strftime('%Y-%m-%d %H:%M')}

💰 *Financial Impact:*
• Current waste: ${financial['cost_per_day']:.2f}/day
• Annual impact: ${financial['cost_per_year']:,.0f}/year
• Potential savings: ${outcome['cost_savings_year']:,.0f}/year

🔧 *Action Required:*
"""
    
    # Add steps
    for step in steps:
        message += f"{step['step']}. {step['action']}\n"
    
    message += f"""
👥 *Responsible:* {steps[0]['responsible']}
⏰ *Deadline:* {priority['urgency']}
📋 *Work Order:* {remediation_plan['work_order_id']}

📊 *Expected Outcome:*
• ROI: {outcome['roi_percent']}
• Payback: {outcome['payback_period']}

_Generated by PlantOPS Action Agent at {datetime.now().strftime('%H:%M')}_ ⚙️"""
    
    return message


def format_chat_response(remediation_plan: Dict[str, Any]) -> str:
    """
    Format remediation plan for watsonx Orchestrate chat
    """
    anomaly = remediation_plan["anomaly_details"]
    priority = remediation_plan["priority"]
    financial = remediation_plan["financial_impact"]
    steps = remediation_plan["remediation_steps"]
    outcome = remediation_plan["expected_outcome"]
    
    response = f"""✅ Remediation plan created successfully!

🚨 **{priority['level']} PRIORITY: {anomaly['type'].replace('_', ' ').title()}**

**Zone:** {anomaly['zone']}
**Impact:** Wasting ${financial['cost_per_day']:.2f}/day (${financial['cost_per_year']:,.0f}/year)

**📋 Work Order:** {remediation_plan['work_order_id']}
**⏰ Deadline:** {priority['urgency']}

**🔧 Action Steps:**
"""
    
    for step in steps:
        response += f"{step['step']}. {step['action']}\n"
    
    response += f"""
**💰 Expected Savings:** ${outcome['cost_savings_year']:,.0f}/year
**📈 ROI:** {outcome['roi_percent']}

**👥 Assigned to:** {steps[0]['responsible']}

_Slack notification sent to maintenance team!_
"""
    
    return response


def get_top_priorities(anomalies: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Rank anomalies by priority and return top N
    """
    priorities = []
    
    for anomaly in anomalies:
        energy_waste = anomaly.get("energy_kwh", 0) - anomaly.get("expected_kwh", 0)
        if energy_waste <= 0:
            continue
        
        financial = calculate_financial_impact(energy_waste)
        priority_info = calculate_priority_score(
            energy_waste,
            financial["cost_per_day"],
            "HIGH" if energy_waste > 100 else "MEDIUM",
            anomaly.get("type", "UNKNOWN")
        )
        
        priorities.append({
            "anomaly": anomaly,
            "priority_score": priority_info["score"],
            "priority_level": priority_info["priority"],
            "annual_savings": financial["potential_annual_savings"],
            "urgency": priority_info["urgency"]
        })
    
    # Sort by priority score descending
    priorities.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return priorities[:limit]
