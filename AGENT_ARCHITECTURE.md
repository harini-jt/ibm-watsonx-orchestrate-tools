# Recommended Agent Architecture for watsonx Orchestrate

## PlantOPS (Main Agent) - Orchestration Layer
The main agent that coordinates all sub-agents.

**Capabilities:**
- Route requests to appropriate agents
- Combine results from multiple agents
- Handle complex multi-step workflows
- Natural language understanding

---

## DataScout Agent - Data Operations (6 endpoints)

### Purpose: Raw data access and basic aggregations

1. **fetch_data**
   - GET /fetch_data
   - Filters: zone_id, shift, date_range, status
   - Returns: Raw manufacturing data

2. **compute_kpis**
   - GET /compute-kpis
   - Calculates: Total energy, CO2, production efficiency
   - Returns: KPI metrics

3. **get_zone_summary** [NEW]
   - GET /zone-summary
   - Aggregates: Energy by zone, production by zone
   - Returns: Zone-level statistics

4. **get_shift_summary** [NEW]
   - GET /shift-summary
   - Aggregates: Performance by shift
   - Returns: Shift comparison data

5. **get_config**
   - GET /config
   - Returns: Current thresholds and parameters

6. **update_config**
   - POST /config
   - Updates: Analysis configuration

---

## Smart Analyzer Agent - Intelligence Operations (8 endpoints)

### Purpose: AI/ML analysis, anomaly detection, forecasting

1. **detect_anomalies_rule_based** [MOVED from DataScout]
   - GET /detect-anomalies
   - Method: Rule-based business logic
   - Returns: Known anomaly patterns

2. **ml_detect_anomalies** [KEEP]
   - GET /ml-detect-anomalies
   - Method: watsonx.ai AutoAI model
   - Returns: AI-detected anomalies with confidence scores

3. **predict_energy** [KEEP]
   - POST /predict-energy
   - Method: watsonx.ai time series model
   - Returns: Energy forecasts (1-168 hours)

4. **compare_detectors** [KEEP]
   - GET /compare-detectors
   - Method: Rule-based vs ML comparison
   - Returns: Detection agreement analysis

5. **plan_actions** [KEEP]
   - GET /plan-actions
   - Method: Generate recommendations from anomalies
   - Returns: Prioritized action items

6. **generate_report** [KEEP]
   - GET /generate-report
   - Method: Comprehensive sustainability report
   - Returns: Full analysis with KPIs, anomalies, actions

7. **run_pipeline** [KEEP]
   - GET /run-pipeline
   - Method: End-to-end analysis orchestration
   - Returns: Complete report

8. **ml_status** [NEW]
   - GET /ml-status
   - Method: Health check for ML models
   - Returns: Model availability status

---

## Visualizer Agent - Presentation Operations (7 endpoints)

### Purpose: Data visualization and report formatting

1. **generate_dashboard**
   - POST /visualizer/dashboard
   - Input: KPIs + anomalies
   - Returns: Complete dashboard JSON config

2. **generate_kpi_cards**
   - POST /visualizer/kpi-cards
   - Input: KPI data
   - Returns: Summary cards with icons and trends

3. **generate_trend_chart**
   - POST /visualizer/trend-chart
   - Input: Time series data
   - Returns: Multi-line chart config (Energy, CO2, Production)

4. **generate_comparison_chart**
   - POST /visualizer/comparison-chart
   - Input: Zone or shift data
   - Returns: Grouped bar chart config

5. **generate_pie_chart**
   - POST /visualizer/pie-chart
   - Input: Categorical data (e.g., energy by zone)
   - Returns: Pie chart config

6. **generate_anomaly_heatmap**
   - POST /visualizer/anomaly-heatmap
   - Input: Anomaly data with timestamps and zones
   - Returns: Heatmap visualization

7. **export_report_pdf**
   - POST /visualizer/export-pdf
   - Input: Report data
   - Returns: PDF download link or base64

---

## Example Workflow: PlantOPS Natural Language Query

**User asks:** "Show me energy anomalies in the paint shop this week"

**PlantOPS orchestrates:**

1. Calls **DataScout.fetch_data**
   - Filters: zone_id="ZONE-PAINT-SHOP", last 7 days
   - Gets: Raw data

2. Calls **Smart Analyzer.ml_detect_anomalies**
   - Input: Paint shop data
   - Gets: 12 anomalies detected

3. Calls **Smart Analyzer.plan_actions**
   - Input: 12 anomalies
   - Gets: 5 prioritized actions

4. Calls **Visualizer.generate_anomaly_heatmap**
   - Input: Anomaly data
   - Gets: Visual heatmap

5. Calls **Visualizer.generate_dashboard**
   - Input: All above data
   - Gets: Complete dashboard

**PlantOPS returns:** "Found 12 anomalies in Paint Shop. Top issue: Paint oven running at 80% energy during zero production on Nov 1st. [View Dashboard]"

---

## Benefits of This Structure:

### 1. Single Responsibility Principle
- DataScout = Data access only
- Smart Analyzer = All intelligence
- Visualizer = All presentation

### 2. Scalability
- Easy to add new ML models to Smart Analyzer
- Easy to add new chart types to Visualizer
- DataScout stays simple and fast

### 3. Reusability
- Visualizer can be used by ANY data source
- Smart Analyzer can work with different datasets
- DataScout is generic data layer

### 4. Testing
- Test data operations independently
- Test ML models independently
- Test visualizations independently

### 5. Natural Language Orchestration
- PlantOPS can intelligently route queries
- "Show me..." → DataScout + Visualizer
- "Predict..." → Smart Analyzer
- "Find anomalies..." → Smart Analyzer
- "Compare..." → DataScout + Smart Analyzer + Visualizer

---

## Implementation Priority:

### Phase 1 (Current - Working):
- ✅ DataScout: fetch_data, compute_kpis, config
- ✅ Smart Analyzer: All ML endpoints working
- ⏳ Visualizer: Not implemented yet

### Phase 2 (Improvements):
1. MOVE `detect-anomalies` from DataScout → Smart Analyzer
2. ADD `get_zone_summary` and `get_shift_summary` to DataScout
3. Implement Visualizer basic endpoints (trend chart, comparison chart)

### Phase 3 (Advanced):
1. ADD `generate_dashboard` to Visualizer
2. ADD `generate_anomaly_heatmap` to Visualizer
3. ADD `export_report_pdf` to Visualizer
4. Improve PlantOPS orchestration logic

---

## Endpoint Count Summary:

| Agent | Endpoints | Status |
|-------|-----------|--------|
| DataScout | 6 | 4 working, 2 new |
| Smart Analyzer | 8 | 7 working, 1 new |
| Visualizer | 7 | 0 working, 7 new |
| **TOTAL** | **21** | **11 working, 10 to build** |

---

## Key Changes from Your Original:

1. ❌ REMOVE: `detect-anomalies` from DataScout
2. ➕ ADD: `detect-anomalies` to Smart Analyzer (where it belongs)
3. ➕ ADD: All ML endpoints to Smart Analyzer
4. ➕ ADD: Zone/Shift summaries to DataScout
5. ➕ ADD: Dashboard generation to Visualizer
6. ➕ ADD: Advanced visualizations (heatmap, cards)

This structure is more aligned with microservices best practices and makes your agents more focused and maintainable! 🚀
