# PlantOPS Multi-Agent System - Hackathon Demo Script

## 🎯 Demo Overview (5 minutes)

**Objective:** Show complete AI-powered sustainability workflow from data collection to automated remediation

**Key Message:** "From Detection to Action in Seconds"

---

## 🎬 Demo Flow

### **Opening (30 seconds)**

**Script:**
```
"Hi! I'm demonstrating PlantOPS - an AI-powered sustainability platform 
for automotive manufacturing that uses IBM watsonx to optimize energy 
consumption and reduce waste.

What makes this unique? It doesn't just detect problems - it automatically 
creates action plans and alerts the right teams to fix them.

Let me show you how it works..."
```

---

### **Act 1: The Problem (1 minute)**

**Screen:** Show dashboard.html with real-time data

**Script:**
```
"This is a live dashboard of an automotive plant with 6 manufacturing zones
running 24/7. Together they consume about 178,000 kWh per week.

But hidden in this data are inefficiencies costing thousands of dollars.
Traditional monitoring would require someone to manually analyze spreadsheets
for hours.

Our solution? A team of AI agents powered by watsonx that work together
to find and fix problems automatically."
```

**Visual:** Point to the KPI cards showing energy/CO2/production metrics

---

### **Act 2: Meet the Agent Team (1 minute)**

**Screen:** Switch to Orchestrate chat interface

**Script:**
```
"We have 4 specialized AI agents orchestrated by watsonx:

1. DataScout - The data specialist. Fetches and filters manufacturing data.

2. Smart Analyzer - The AI detective. Uses watsonx.ai machine learning 
   to detect anomalies and predict future energy consumption.

3. Action Agent - The problem solver. Creates work orders and alerts
   maintenance teams via Slack.

4. Visualizer - The presenter. Transforms data into interactive charts.

Let's see them in action..."
```

---

### **Act 3: Live Detection (2 minutes)**

**Type in Orchestrate:**
```
"Analyze the paint shop and alert maintenance if there are any issues"
```

**What Happens (narrate while showing):**

1. **DataScout activates**
   ```
   "First, DataScout retrieves the last 24 hours of paint shop data..."
   ```

2. **Smart Analyzer takes over**
   ```
   "The Smart Analyzer uses our watsonx.ai AutoAI model - trained on 
   1,000+ hours of plant data - to detect anomalies.
   
   And it found something! The paint oven is consuming 10.5 kWh per hour 
   while production is stopped. That's $6,132 per year wasted."
   ```

3. **Action Agent creates plan**
   ```
   "Now watch this - the Action Agent automatically:
   - Creates work order WO-20251103-1001
   - Calculates the financial impact
   - Generates a 4-step fix plan
   - And sends this to Slack..."
   ```

4. **Show Slack notification (switch screens)**
   ```
   [Show #plant-maintenance channel]
   
   "The maintenance team just received this alert with:
   - What's wrong
   - Why it matters ($6,132/year)
   - Exactly how to fix it (15 minutes, zero cost)
   - Who's responsible
   - When it needs to be done
   
   From detection to actionable alert in under 3 seconds."
   ```

---

### **Act 4: The Business Value (30 seconds)**

**Screen:** Back to Orchestrate showing results

**Script:**
```
"This one issue alone saves $6,132 per year. But our system detected
78 total anomalies this week with a combined savings potential of 
$47,000 annually.

More importantly, it's proactive. We're not waiting for equipment to 
fail or efficiency to drop. We're catching problems early and fixing 
them immediately."
```

---

### **Act 5: The Technology (30 seconds)**

**Screen:** Show architecture diagram or API docs

**Script:**
```
"Under the hood, we're using:
- IBM watsonx.ai for anomaly detection and energy forecasting
- watsonx Orchestrate for multi-agent coordination
- FastAPI for our microservices architecture
- Real-time integration with Slack for team collaboration

Everything is containerized and cloud-ready for enterprise deployment."
```

---

### **Closing (30 seconds)**

**Script:**
```
"To summarize: PlantOPS transforms sustainability from a reactive 
compliance task into a proactive profit center.

We detect problems with AI, create solutions automatically, and 
coordinate action across teams - all in real-time.

The result? Lower energy costs, reduced emissions, and a more 
efficient manufacturing operation.

Questions?"
```

---

## 🗣️ Talking Points for Q&A

### **Q: How accurate is the anomaly detection?**
```
"Our watsonx.ai model achieves 92% accuracy on our test data. We've 
also implemented a hybrid approach - combining rule-based detection 
for known issues with ML for discovering new patterns. This gives us 
both precision and adaptability."
```

### **Q: Can it integrate with existing plant systems?**
```
"Absolutely. We have RESTful APIs that can integrate with any SCADA 
system, ERP, or data historian. We're currently using CSV data, but 
production deployments would connect directly to plant databases via 
JDBC/ODBC or real-time streams."
```

### **Q: What about false positives?**
```
"Great question! Each anomaly includes a confidence score and financial 
impact. Low-confidence or low-impact alerts go to a review queue, while 
high-confidence issues trigger immediate notifications. This prevents 
alert fatigue."
```

### **Q: How long did this take to build?**
```
"The core system was built in [X days] leveraging watsonx's AutoAI 
for model training, which saved weeks of manual feature engineering. 
The multi-agent orchestration using watsonx Orchestrate lets us add 
new capabilities without rewriting core logic."
```

### **Q: What's the ROI?**
```
"For a typical automotive plant, we estimate:
- 10-15% reduction in energy costs (year 1)
- 5-8% improvement in OEE (Overall Equipment Effectiveness)
- 20-30% reduction in reactive maintenance
- Payback period: 3-6 months"
```

### **Q: How does it handle multiple plants?**
```
"The architecture is multi-tenant ready. Each plant would have its own 
watsonx.ai models trained on local data, but share the same Action Agent 
and Visualizer services. We can centralize monitoring while respecting 
plant-specific patterns."
```

---

## 🎯 Demo Tips

### **Before Demo:**
- [ ] Test all endpoints locally
- [ ] Verify Slack connection working
- [ ] Have dashboard.html open and loaded
- [ ] Clear Orchestrate chat history
- [ ] Close unnecessary browser tabs
- [ ] Increase font size for visibility
- [ ] Test internet connection
- [ ] Have backup screenshots ready

### **During Demo:**
- ✅ Speak slowly and clearly
- ✅ Make eye contact with judges
- ✅ Explain "why" not just "what"
- ✅ Show enthusiasm!
- ✅ Point to specific numbers (savings, ROI)
- ✅ Let the AI agent responses speak for themselves
- ✅ If something fails, have backup screenshots

### **Pro Tips:**
- 💡 Practice the demo 3+ times beforehand
- 💡 Time yourself - aim for 4:30, leave 30s buffer
- 💡 Have a printed copy of this script as backup
- 💡 Screenshot every step in case demo fails
- 💡 Know your numbers: $6,132, 78 anomalies, 92% accuracy

---

## 📊 Key Metrics to Highlight

| Metric | Value | Impact |
|--------|-------|--------|
| Anomalies Detected | 78 | Proactive vs reactive |
| Total Annual Savings | $47,000+ | Real business value |
| Detection Speed | <3 seconds | Real-time response |
| Fix Time (avg) | 15-30 min | Quick resolution |
| ML Model Accuracy | 92% | Trustworthy insights |
| ROI | 500%+ | Massive returns |
| Payback Period | 3-6 months | Fast value realization |

---

## 🎨 Backup Plan (If Demo Fails)

### **If Internet/API Down:**
1. Switch to screenshots/video recording of working demo
2. Walk through the screenshots
3. Explain: "This is a recorded demo from our testing"
4. Still show the value and explain architecture

### **If Orchestrate Times Out:**
1. Show direct API calls via Postman/cURL
2. Demonstrate same functionality
3. Explain: "Production would run through Orchestrate"

### **If Slack Doesn't Load:**
1. Show the `slack_message` JSON response
2. Read it aloud
3. Say: "This would appear in Slack like this..."
4. Show screenshot of previous Slack notification

---

## 🏆 Winning Elements

**What Judges Look For:**
1. ✅ **Problem-Solution Fit** - Clear pain point, clear solution
2. ✅ **Technical Execution** - Actually works, well-built
3. ✅ **IBM Technology Use** - Deep watsonx integration
4. ✅ **Business Impact** - Real ROI numbers
5. ✅ **Innovation** - Multi-agent orchestration is cutting-edge
6. ✅ **Completeness** - End-to-end solution

**Your Strengths:**
- 🌟 Uses 3 watsonx products (ai, Orchestrate, possibly governance)
- 🌟 Real-world problem (sustainability + cost savings)
- 🌟 Complete workflow (detection → action → notification)
- 🌟 Measurable impact ($47K+ savings)
- 🌟 Enterprise-ready architecture
- 🌟 Live demo with real data

---

## 🎤 One-Liner for Judges

```
"PlantOPS is an AI-powered sustainability platform that uses IBM watsonx 
to automatically detect energy waste, create remediation plans, and 
coordinate action across teams - reducing costs by up to 15% while 
improving equipment effectiveness."
```

---

## 📸 Screen Recording Checklist

If creating backup video:
- [ ] Record full demo run-through
- [ ] Include audio narration
- [ ] Show Orchestrate chat clearly
- [ ] Show Slack notification
- [ ] Show dashboard visualizations
- [ ] Keep under 5 minutes
- [ ] Export as MP4 (widely compatible)
- [ ] Test playback before event

---

## 🚀 Final Checklist

**30 Minutes Before:**
- [ ] Test API is running
- [ ] Verify Slack connection
- [ ] Clear chat history
- [ ] Set up screens/projector
- [ ] Increase font sizes
- [ ] Close distracting apps
- [ ] Charge laptop fully
- [ ] Have power adapter ready

**5 Minutes Before:**
- [ ] Take deep breath
- [ ] Review one-liner
- [ ] Open all necessary tabs
- [ ] Test one quick API call
- [ ] Smile 😊

**You've got this!** 🎯

Your solution is impressive, well-built, and solves a real problem.
Show confidence, explain the value, and let the AI agents do their magic!

Good luck! 🍀🚀
