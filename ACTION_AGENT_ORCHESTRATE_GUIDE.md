# Action Agent (Remedy Agent) - watsonx Orchestrate Configuration Guide

## 🎯 Overview

The Action Agent receives anomaly data from Smart Analyzer, creates remediation plans with work orders, and sends Slack notifications to your maintenance team.

---

## 📋 Action Agent Skills to Add in Orchestrate

### **Skill 1: Create Remediation Plan** ⭐ (Most Important)

**Description:**
```
Creates a comprehensive remediation plan for detected anomalies. Generates work orders, calculates financial impact, provides step-by-step fix instructions, and formats Slack notifications for the maintenance team.
```

**API Configuration:**
- **Method:** POST
- **URL:** `https://your-api.com/actions/create-remediation?format=chat&send_slack=true`
- **Content-Type:** application/json

**Input Parameters:**
```json
{
  "type": {
    "type": "string",
    "description": "Anomaly type (PAINT_OVEN_IDLE, COMPRESSED_AIR_LEAK, etc.)",
    "required": true
  },
  "zone": {
    "type": "string",
    "description": "Zone ID where anomaly was detected",
    "required": true
  },
  "energy_waste_kwh": {
    "type": "number",
    "description": "Energy waste in kWh per hour",
    "required": true
  },
  "severity": {
    "type": "string",
    "description": "Severity level: HIGH, MEDIUM, or LOW",
    "default": "MEDIUM"
  },
  "note": {
    "type": "string",
    "description": "Additional notes about the anomaly",
    "required": false
  }
}
```

**Example Request:**
```json
{
  "type": "PAINT_OVEN_IDLE",
  "zone": "ZONE-PAINT-SHOP",
  "energy_waste_kwh": 10.5,
  "severity": "HIGH",
  "note": "Paint oven running during 2-hour production gap"
}
```

**Response in Orchestrate Chat:**
```
✅ Remediation plan created successfully!

🚨 HIGH PRIORITY: Paint Oven Idle

Zone: ZONE-PAINT-SHOP
Impact: Wasting $16.80/day ($6,132/year)

📋 Work Order: WO-20251103-1001
⏰ Deadline: Action required within 24 hours

🔧 Action Steps:
1. Inspect paint oven timer settings
2. Verify auto-shutdown during production gaps
3. Test timer with production schedule
4. Document timer configuration in maintenance log

💰 Expected Savings: $6,132/year
📈 ROI: ∞

👥 Assigned to: Maintenance Team

_Slack notification sent to maintenance team!_
```

**Response Field for Orchestrate:** `message`

---

### **Skill 2: Get Priority Actions**

**Description:**
```
Ranks all detected anomalies by priority and returns the top actions based on financial impact and urgency. Helps teams focus on highest-value fixes first.
```

**API Configuration:**
- **Method:** GET
- **URL:** `https://your-api.com/actions/priorities?format=chat&limit=5`

**Query Parameters:**
```json
{
  "zone_id": {
    "type": "string",
    "description": "Filter by zone (optional)",
    "required": false
  },
  "limit": {
    "type": "integer",
    "description": "Number of priorities to return (default: 5)",
    "default": 5
  }
}
```

**Response in Chat:**
```
🎯 Top 5 Priority Actions

1. Paint Oven Idle (CRITICAL)
   Zone: ZONE-PAINT-SHOP
   Potential Savings: $6,132/year
   Immediate action required (within 2 hours)

2. Compressed Air Leak (HIGH)
   Zone: ZONE-BODY-SHOP
   Potential Savings: $4,380/year
   Action required within 24 hours

3. HVAC Inefficiency (MEDIUM)
   Zone: ZONE-ASSEMBLY
   Potential Savings: $2,555/year
   Schedule within 3 days

Total Potential Savings: $13,067/year
```

---

### **Skill 3: Estimate Impact**

**Description:**
```
Calculates the financial impact of energy waste. Provides cost breakdown per hour, day, month, and year to help prioritize actions.
```

**API Configuration:**
- **Method:** POST
- **URL:** `https://your-api.com/actions/estimate-impact?format=chat`

**Query Parameters:**
```json
{
  "energy_waste_kwh": {
    "type": "number",
    "description": "Energy waste in kWh per hour",
    "required": true
  },
  "duration_days": {
    "type": "integer",
    "description": "Duration to calculate (default: 365 days)",
    "default": 365
  }
}
```

**Example:**
```
GET /actions/estimate-impact?energy_waste_kwh=10.5&duration_days=365&format=chat
```

**Response:**
```
💰 Financial Impact Estimation

Energy Waste: 10.5 kWh/hour

Cost Breakdown:
• Per hour: $0.74
• Per day: $17.64
• Per month: $529.20
• Per year: $6,440.40

Over 365 days: $6,440.40

💡 Fixing this issue could save $6,440.40 annually!
```

---

### **Skill 4: Work Order Status**

**Description:**
```
Tracks the status of a work order. Shows progress, assigned team, and updates.
```

**API Configuration:**
- **Method:** GET
- **URL:** `https://your-api.com/actions/work-order/{work_order_id}`

**Path Parameters:**
```json
{
  "work_order_id": {
    "type": "string",
    "description": "Work order ID to query (e.g., WO-20251103-1001)",
    "required": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "work_order": {
    "work_order_id": "WO-20251103-1001",
    "status": "IN_PROGRESS",
    "progress": "60%",
    "assigned_to": "Maintenance Team",
    "estimated_completion": "2025-11-03T16:30:00Z",
    "updates": [...]
  }
}
```

---

### **Skill 5: Preview Slack Message**

**Description:**
```
Preview what the Slack notification will look like without actually sending it. Useful for testing.
```

**API Configuration:**
- **Method:** GET
- **URL:** `https://your-api.com/actions/slack-preview`

**Query Parameters:**
```json
{
  "anomaly_type": {
    "type": "string",
    "description": "Anomaly type",
    "required": true
  },
  "zone": {
    "type": "string",
    "description": "Zone ID",
    "required": true
  },
  "energy_waste_kwh": {
    "type": "number",
    "description": "Energy waste kWh/hour",
    "required": true
  }
}
```

---

## 🔗 Connecting Slack in watsonx Orchestrate

### **Method 1: Use Orchestrate's Slack Skill** (Easiest)

**Step 1: Add Slack Skill**
1. In Orchestrate, go to Skills Catalog
2. Search for "Slack"
3. Click "Add skill"
4. Authorize with your Slack workspace

**Step 2: Create Multi-Skill Flow**
```
User Query: "Check anomalies and alert maintenance team"
    ↓
PlantOPS orchestrates:
    1. Smart Analyzer → detect_anomalies
    2. Action Agent → create_remediation (returns slack_message)
    3. Slack Skill → send_message
       - Channel: #plant-maintenance
       - Message: {action_agent.slack_message}
```

**Step 3: Configure Slack Message**
In the Slack skill configuration:
- **Channel:** `#plant-maintenance` (create this channel in Slack)
- **Message Source:** Use `slack_message` field from Action Agent response
- **Thread:** Start new thread
- **Mention:** @maintenance-team

---

### **Method 2: Use Slack Webhook in Action Agent** (Direct Integration)

If Orchestrate's Slack skill doesn't work, use this:

**Step 1: Get Slack Webhook URL**
1. Go to https://api.slack.com/messaging/webhooks
2. Click "Create New Webhook"
3. Choose channel: `#plant-maintenance`
4. Copy webhook URL: `https://hooks.slack.com/services/T.../B.../XXX`

**Step 2: Add to .env file**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../XXX
```

**Step 3: Update action_agent.py**
```python
import requests
import os

def send_to_slack(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "not_configured"}
    
    response = requests.post(webhook_url, json={"text": message})
    return {"status": "sent" if response.status_code == 200 else "failed"}
```

**Step 4: Modify endpoint in main.py**
```python
@app.post("/actions/create-remediation")
def create_remediation(..., auto_send_slack: bool = False):
    plan = generate_remediation_plan(...)
    
    if auto_send_slack:
        slack_msg = format_slack_message(plan)
        result = send_to_slack(slack_msg)
        plan["slack_sent"] = result["status"] == "sent"
    
    return plan
```

---

## 🎬 Complete Demo Flow

### **Scenario: End-to-End Anomaly Remediation**

**User asks PlantOPS:**
```
"Analyze the paint shop and alert maintenance if there are any issues"
```

**PlantOPS orchestrates (behind the scenes):**

```
Step 1: DataScout.fetch_data
  → Gets paint shop data for last 24 hours
  
Step 2: Smart Analyzer.ml_detect_anomalies
  → Detects: Paint oven idle anomaly (10.5 kWh waste)
  
Step 3: Action Agent.create_remediation
  → Creates work order WO-20251103-1001
  → Calculates impact: $6,132/year savings
  → Generates 4-step fix plan
  → Formats Slack message
  
Step 4: Slack.send_message
  → Sends to #plant-maintenance channel
  → Mentions @maintenance-team
  → Creates alert thread
```

**PlantOPS responds to user:**
```
✅ Analysis complete!

Found 1 high-priority issue in Paint Shop:
• Paint Oven Idle - wasting $6,132/year

🚨 Remediation plan created (Work Order: WO-20251103-1001)
📲 Maintenance team notified via Slack
⏰ Deadline: Within 24 hours
💰 Potential savings: $6,132/year

The team can fix this in 15 minutes with zero cost!
```

**Meanwhile, in Slack #plant-maintenance:**
```
[Notification appears]

🚨 HIGH PRIORITY ALERT

Anomaly Detected: Paint Oven Idle
Zone: ZONE-PAINT-SHOP
Category: Equipment Misuse
Detected: 2025-11-03 14:30

💰 Financial Impact:
• Current waste: $16.80/day
• Annual impact: $6,132/year
• Potential savings: $6,132/year

🔧 Action Required:
1. Inspect paint oven timer settings
2. Verify auto-shutdown during production gaps
3. Test timer with production schedule
4. Document timer configuration in maintenance log

👥 Responsible: Maintenance Team
⏰ Deadline: Action required within 24 hours
📋 Work Order: WO-20251103-1001

📊 Expected Outcome:
• ROI: ∞
• Payback: Immediate

Generated by PlantOPS Action Agent at 14:30 ⚙️

[React: ✅ when completed | 🚧 in progress | ❌ blocked]
```

---

## 🔧 Testing Your Configuration

### **Test 1: Create Remediation**
```bash
curl -X POST "http://localhost:8000/actions/create-remediation?format=chat&send_slack=true" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "PAINT_OVEN_IDLE",
    "zone": "ZONE-PAINT-SHOP",
    "energy_waste_kwh": 10.5,
    "severity": "HIGH"
  }'
```

**Expected:** Chat-formatted response with work order and Slack message

### **Test 2: Get Priorities**
```bash
curl "http://localhost:8000/actions/priorities?format=chat&limit=3"
```

**Expected:** Top 3 priority actions with savings

### **Test 3: Preview Slack**
```bash
curl "http://localhost:8000/actions/slack-preview?anomaly_type=COMPRESSED_AIR_LEAK&zone=ZONE-BODY-SHOP&energy_waste_kwh=5"
```

**Expected:** Formatted Slack message preview

---

## 📊 Supported Anomaly Types

The Action Agent handles these anomaly types with pre-configured remediation plans:

1. **PAINT_OVEN_IDLE** - Equipment running while idle
2. **COMPRESSED_AIR_LEAK** - Air pressure system leak
3. **HVAC_INEFFICIENCY** - Climate control waste
4. **STANDBY_POWER_EXCESSIVE** - Equipment left running
5. **PRODUCTION_EFFICIENCY_DROP** - Process optimization needed

Each has:
- ✅ Root cause analysis
- ✅ Step-by-step fix instructions
- ✅ Time and cost estimates
- ✅ Assigned teams
- ✅ Expected ROI

---

## 🎯 Quick Start Prompts for Orchestrate

**Prompt 1:**
```
"Check for anomalies in the paint shop and create remediation plans"
```

**Prompt 2:**
```
"What are the top 5 priority actions to save energy?"
```

**Prompt 3:**
```
"Calculate the cost of wasting 15 kWh per hour for a year"
```

**Prompt 4:**
```
"Analyze all zones, find problems, and alert the maintenance team on Slack"
```

---

## ✅ Configuration Checklist

- [ ] Action Agent endpoints added to main.py
- [ ] Test all endpoints locally
- [ ] Add Action Agent skills to watsonx Orchestrate
- [ ] Configure skill URLs with `?format=chat`
- [ ] Set up Slack channel (#plant-maintenance)
- [ ] Connect Slack to Orchestrate OR configure webhook
- [ ] Test end-to-end flow
- [ ] Prepare demo script
- [ ] Create sample anomaly for demo
- [ ] Screenshot Slack notification for backup

---

## 🚀 You're Ready!

Your Action Agent is now fully integrated and ready to:
- ✅ Analyze anomalies
- ✅ Create work orders
- ✅ Calculate ROI
- ✅ Send Slack notifications
- ✅ Track priorities

**This completes your multi-agent architecture:**
DataScout → Smart Analyzer → Action Agent → Visualizer + Slack! 🎉
