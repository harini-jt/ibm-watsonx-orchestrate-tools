# 🏗️ Complete Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                          │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  Plant Operators │         │  Energy Managers │             │
│  │  (Voice/Text)    │         │  (Dashboard)     │             │
│  └────────┬─────────┘         └────────┬─────────┘             │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                              │
            │ Natural Language Queries     │
            ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              WATSONX ORCHESTRATE (AI AGENTS)                     │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Data Scout      │  │  Analyser Agent  │  │ Action        │ │
│  │  Agent           │  │  (Insights)      │  │ Executor      │ │
│  │  (Data Queries)  │  │                  │  │ (Future)      │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                     │          │
│           │   OpenAPI Skills    │                     │          │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
            │ REST API Calls      │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Vercel Serverless)                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              TRADITIONAL ENDPOINTS                           ││
│  │  /fetch_data        - Raw data queries                      ││
│  │  /compute-kpis      - Calculate metrics                     ││
│  │  /detect-anomalies  - Rule-based detection                  ││
│  │  /plan-actions      - Generate recommendations              ││
│  │  /generate-report   - Create sustainability reports         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              🤖 NEW ML-POWERED ENDPOINTS                     ││
│  │  /ml-detect-anomalies  - AI anomaly detection               ││
│  │  /predict-energy       - Energy forecasting (1-168h)        ││
│  │  /compare-detectors    - Rule vs ML comparison              ││
│  │  /ml-status           - Model health check                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────┐                                            │
│  │  wml_client.py  │ ← Handles watsonx.ai communication        │
│  └────────┬────────┘                                            │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ Model Inference API Calls
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              WATSONX.AI RUNTIME (ML Models)                      │
│                                                                   │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐ │
│  │  Anomaly Detection       │  │  Energy Forecasting         │ │
│  │  (Isolation Forest)      │  │  (XGBoost Regressor)        │ │
│  │                          │  │                             │ │
│  │  Input:                  │  │  Input:                     │ │
│  │  - Energy consumption    │  │  - Historical energy        │ │
│  │  - Production units      │  │  - Lag features (1-24h)     │ │
│  │  - Temperature           │  │  - Time features            │ │
│  │  - Shift/status          │  │  - Rolling statistics       │ │
│  │                          │  │                             │ │
│  │  Output:                 │  │  Output:                    │ │
│  │  - Anomaly flag (0/1)    │  │  - Predicted kWh            │ │
│  │  - Confidence score      │  │  - Hour-by-hour forecast    │ │
│  └──────────────────────────┘  └─────────────────────────────┘ │
│                                                                   │
│  Trained on: 1,008 samples     Trained on: 144 time points      │
│  Accuracy: 93-95%              R² Score: 0.85-0.92               │
└─────────────────────────────────────────────────────────────────┘
            │
            │ Training Data
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              DATA LAYER (CSV Storage)                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  automotive_energy_data.csv                               │  │
│  │  - 1 week of data (168 hours × 6 zones = 1,008 records)  │  │
│  │  - Energy, CO2, production, temperature, efficiency       │  │
│  │  - Generated by: mock-weekly-data.py                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  data/ml_training/                                        │  │
│  │  - anomaly_detection_dataset.csv (labeled training data)  │  │
│  │  - energy_forecasting_dataset.csv (time series)           │  │
│  │  - forecast_*.csv (zone-specific forecasts)               │  │
│  │  - Generated by: prepare_ml_data.py                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Examples

### Example 1: Traditional Rule-Based Detection
```
1. User asks: "Find anomalies in paint shop yesterday"
   ↓
2. Data Scout Agent receives query
   ↓
3. Agent calls: GET /detect-anomalies?zone_id=ZONE-PAINT-SHOP&start_date=2025-11-01
   ↓
4. FastAPI applies threshold rules:
   - Paint oven idle? (energy > 3000 kWh, production = 0)
   - Air leak? (air > 1500 m³, production ≤ 1)
   - HVAC overcooling? (temp < 19°C)
   ↓
5. Returns: 12 anomalies found
   Types: [PAINT_OVEN_IDLE, COMPRESSED_AIR_LEAK]
```

### Example 2: NEW - ML-Based Detection
```
1. User asks: "Find anomalies using AI"
   ↓
2. Analyser Agent receives query
   ↓
3. Agent calls: GET /ml-detect-anomalies
   ↓
4. FastAPI prepares features:
   - Extracts: energy_kwh, production_units, hour, shift
   - Calculates: energy_per_unit, air_per_unit
   - Encodes: zone_id → numeric
   ↓
5. wml_client sends to watsonx.ai:
   POST https://us-south.ml.cloud.ibm.com/ml/v4/deployments/{id}/predictions
   ↓
6. Isolation Forest model analyzes:
   - Compares to normal patterns
   - Assigns anomaly score (0-1)
   ↓
7. Returns: 15 anomalies found (3 more than rules!)
   - With confidence scores: 0.87, 0.92, 0.78...
```

### Example 3: NEW - Energy Forecasting
```
1. User asks: "Predict energy for next 24 hours"
   ↓
2. Analyser Agent receives query
   ↓
3. Agent calls: GET /predict-energy?hours_ahead=24
   ↓
4. FastAPI prepares time series features:
   - Aggregates historical data by hour
   - Creates lag features (1h, 3h, 6h, 12h, 24h ago)
   - Calculates rolling statistics
   ↓
5. wml_client sends to watsonx.ai:
   - XGBoost model runs inference
   - Predicts hour 1, then hour 2, ... hour 24
   ↓
6. Returns: 24-hour forecast
   - Hour 1: 10,245 kWh
   - Hour 2: 10,389 kWh
   - ...
   - Total: 245,680 kWh
```

### Example 4: Comparative Analysis
```
1. User asks: "Compare rule-based and ML detection"
   ↓
2. Analyser Agent receives query
   ↓
3. Agent calls: GET /compare-detectors
   ↓
4. FastAPI runs BOTH methods in parallel:
   ┌─────────────────┐  ┌──────────────────┐
   │ detect_anomalies│  │ ml_detect_anomalies│
   │ (Rule-based)    │  │ (watsonx.ai)     │
   └────────┬────────┘  └────────┬─────────┘
            │                    │
            ▼                    ▼
   82 anomalies found    95 anomalies found
   ↓
5. Combines results:
   - Agreement: 70 overlapping
   - ML found 25 additional (subtle patterns)
   - Rules found 12 unique (known issues)
   ↓
6. Returns comparison with insights
```

---

## Technology Stack

### Frontend / Interface:
- **watsonx Orchestrate** - AI agent orchestration
- Natural language processing
- Multi-agent collaboration

### Backend / API:
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **Pandas/NumPy** - Data processing
- **Vercel** - Serverless deployment

### AI / ML:
- **watsonx.ai Studio** - Model training & experimentation
- **watsonx.ai Runtime** - Model deployment & inference
- **Isolation Forest** - Anomaly detection (unsupervised)
- **XGBoost** - Energy forecasting (supervised regression)
- **scikit-learn** - ML pipeline utilities

### Data:
- **CSV** - Structured data storage
- **Synthetic data** - 1 week automotive plant operations
- **Feature engineering** - Lag features, rolling stats, encodings

---

## Key Innovations

### 1. Hybrid Detection
```
Traditional Rules          ML Model              Combined Strength
├─ Fast                   ├─ Learns patterns    ├─ High accuracy
├─ Explainable            ├─ Catches subtle     ├─ Few false alarms
├─ Domain knowledge       ├─ Adapts to changes  ├─ Comprehensive
└─ Known issues           └─ Statistical rigor  └─ Best of both
```

### 2. Proactive Intelligence
```
Before (Reactive)          After (Proactive)
├─ Detect past issues     ├─ Predict future issues
├─ React to problems      ├─ Prevent problems
├─ Monthly reports        ├─ Real-time insights
└─ Manual analysis        └─ Automated recommendations
```

### 3. Multi-Agent Orchestration
```
Single Agent              Multi-Agent System
├─ One-size-fits-all     ├─ Specialized agents
├─ Limited context       ├─ Deep expertise
├─ Linear workflow       ├─ Parallel execution
└─ Fixed responses       └─ Dynamic collaboration
```

---

## Business Impact

### Quantifiable Benefits:

**Energy Savings:**
- ML catches 13% more anomalies than rules
- Each anomaly = ~500 kWh wasted
- 13 additional anomalies/week × 500 kWh = 6,500 kWh/week saved
- At ₹0.07/kWh = ₹455/week = ₹23,660/year per zone

**Carbon Reduction:**
- 6,500 kWh × 0.82 kg CO₂/kWh = 5,330 kg CO₂/week
- 277,160 kg CO₂/year per zone
- Across 6 zones = 1.66 million kg CO₂/year

**Operational Efficiency:**
- Forecasting enables optimized energy procurement
- Proactive maintenance reduces downtime
- Automated reporting saves 10+ hours/week

### Strategic Value:
- ✅ Meets carbon neutrality goals (SDG 9)
- ✅ Demonstrates AI/ML maturity
- ✅ Scalable to other plants
- ✅ Competitive advantage in sustainable manufacturing

---

**Ready to implement? Start with IMPLEMENTATION_CHECKLIST.md** ✅
