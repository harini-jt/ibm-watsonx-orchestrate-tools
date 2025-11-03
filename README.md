# GreenOps: Automotive Manufacturing Sustainability API

> AI-powered sustainability platform for automotive manufacturing plants using IBM watsonx

[![Vercel Deployment](https://img.shields.io/badge/Deployed%20on-Vercel-black)](https://data-gov-apis.vercel.app)
[![IBM watsonx](https://img.shields.io/badge/Powered%20by-IBM%20watsonx-blue)](https://www.ibm.com/watsonx)

## 🎯 Problem Statement

Automotive manufacturing plants struggle to monitor energy consumption, detect operational anomalies, and forecast resource needs in real-time. This leads to:
- 🔴 **Energy waste** from idle equipment and inefficient operations
- 🔴 **Increased CO₂ emissions** and environmental impact
- 🔴 **Reactive maintenance** instead of predictive insights
- 🔴 **Manual analysis** of complex operational data

## 💡 Solution

**GreenOps** is an AI-powered API platform that provides:
- ✅ **Real-time anomaly detection** using watsonx.ai ML models
- ✅ **Energy consumption forecasting** for predictive planning
- ✅ **Multi-agent orchestration** via watsonx Orchestrate
- ✅ **Automated sustainability KPIs** and actionable recommendations

## 🚀 Key Features

### 1. **Intelligent Anomaly Detection**
- ML-powered Isolation Forest model (trained in watsonx.ai)
- Detects paint oven idle waste, compressed air leaks, HVAC inefficiencies
- 7.74% anomaly rate with high-confidence scoring

### 2. **Energy Forecasting**
- XGBoost time series model predicting 1-168 hours ahead
- Recursive forecasting with lag features
- Enables proactive resource planning

### 3. **Multi-Agent Orchestration**
- **Data Scout Agent**: Fetches operational data and detects anomalies
- **Analyser Agent**: Computes KPIs and forecasts energy consumption
- Natural language interface via watsonx Orchestrate

### 4. **Comprehensive APIs**
11 REST endpoints for:
- Operational data queries
- KPI computation (energy, CO₂, efficiency)
- Anomaly detection (rule-based + ML)
- Energy forecasting
- Actionable recommendations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    watsonx Orchestrate                      │
│  (Natural Language → Multi-Agent Orchestration)             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─► Data Scout Agent (Fetch + Detect)
                 └─► Analyser Agent (Compute + Forecast)
                 │
┌────────────────▼────────────────────────────────────────────┐
│              FastAPI Backend (main.py)                      │
│  • 11 REST Endpoints                                        │
│  • Pydantic Validation                                      │
│  • Deployed on Vercel Serverless                            │
└────────────────┬────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────┐      ┌───────▼────────┐
│  CSV Data │      │  watsonx.ai ML │
│  1008 rows│      │  • Anomaly Det │
│  168 hours│      │  • Forecasting │
│  6 zones  │      │  AutoAI Models │
└───────────┘      └────────────────┘
```

## 📊 Results & Impact

**From 168-hour dataset (Oct 27 - Nov 2, 2025):**
- 🎯 **78 anomalies detected** (7.74% of operations)
- 💰 **₹1.42 Lakh potential savings** from anomaly prevention
- 🌱 **1.66M kg CO₂ reduction** possible
- 📈 **95% prediction accuracy** for energy forecasting

**Comparison: Rule-based vs ML**
| Method | Anomalies Detected | Detection Rate |
|--------|-------------------|----------------|
| Rule-based | 80 | 7.94% |
| ML (watsonx.ai) | 78 | 7.74% |
| Agreement | High overlap | Both effective |

## 🛠️ Technology Stack

- **Backend**: FastAPI 3.x, Python 3.9, Pydantic
- **ML Platform**: IBM watsonx.ai (AutoAI, Isolation Forest, XGBoost)
- **Orchestration**: IBM watsonx Orchestrate (Multi-agent system)
- **Deployment**: Vercel (Serverless)
- **Data**: Synthetic automotive plant data (1,008 records)

## 📡 API Endpoints

### Core Data Endpoints
- `GET /fetch_data` - Query operational data with filters
- `GET /compute-kpis` - Calculate sustainability KPIs

### Anomaly Detection
- `GET /detect-anomalies` - Rule-based detection
- `GET /ml-detect-anomalies` - AI-powered detection ⭐
- `GET /compare-detectors` - Compare rule vs ML methods

### Forecasting & Planning
- `GET /predict-energy` - Forecast 1-168 hours ahead ⭐
- `GET /plan-actions` - Get actionable recommendations

### System
- `GET /ml-status` - Check ML model health
- `GET /docs` - Interactive API documentation

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/harini-jt/data-gov-apis.git
cd data-gov-apis
```

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Create .env file
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id
WATSONX_SPACE_ID=your_space_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
ANOMALY_DEPLOYMENT_ID=your_anomaly_model_id
FORECAST_DEPLOYMENT_ID=your_forecast_model_id
```

### 4. Run Development Server
```bash
uvicorn main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## 📖 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed system design
- **[ML_INTEGRATION_README.md](./ML_INTEGRATION_README.md)** - ML model training & deployment
- **[START_HERE.md](./START_HERE.md)** - Beginner's guide
- **[SUMMARY.md](./SUMMARY.md)** - Project overview & demo script

## 🧪 Testing

```bash
# Test watsonx.ai integration
python test_watsonx_integration.py

# Test ML endpoints
curl http://localhost:8000/ml-detect-anomalies
curl http://localhost:8000/predict-energy?hours_ahead=24
```

## 🌐 Live Demo

**Production API**: [https://data-gov-apis.vercel.app](https://data-gov-apis.vercel.app)

**Try it:**
```bash
curl https://data-gov-apis.vercel.app/compute-kpis
```

## 🏆 IBM watsonx Integration

This project showcases:
1. **watsonx.ai** - ML model training (AutoAI) and deployment
2. **watsonx Orchestrate** - Multi-agent orchestration with natural language
3. **Real-world use case** - Manufacturing sustainability optimization

## 📄 License

MIT License - See LICENSE file for details

## 👥 Team

Created for IBM watsonx Hackathon 2025

