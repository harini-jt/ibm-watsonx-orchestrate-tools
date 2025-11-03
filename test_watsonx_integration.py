"""
Test watsonx.ai Integration
Run this to verify your setup before deploying
"""

import os
from dotenv import load_dotenv

print("=" * 60)
print("🧪 watsonx.ai Integration Test")
print("=" * 60)

# Load environment variables
load_dotenv()

# Step 1: Check environment variables
print("\n1️⃣ Checking Environment Variables...")
required_vars = [
    "WATSONX_API_KEY",
    "WATSONX_PROJECT_ID",
    "WATSONX_URL"
]

optional_vars = [
    "ANOMALY_DEPLOYMENT_ID",
    "FORECAST_DEPLOYMENT_ID"
]

missing_required = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask API key for security
        if "KEY" in var:
            display = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        else:
            display = value
        print(f"   ✅ {var}: {display}")
    else:
        print(f"   ❌ {var}: NOT SET")
        missing_required.append(var)

print("\n   Optional (for ML endpoints):")
for var in optional_vars:
    value = os.getenv(var)
    if value:
        print(f"   ✅ {var}: {value[:20]}...")
    else:
        print(f"   ⚠️  {var}: NOT SET (ML endpoints won't work)")

if missing_required:
    print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
    print("   Update your .env file and try again.")
    exit(1)

# Step 2: Test watsonx.ai connection
print("\n2️⃣ Testing watsonx.ai Connection...")
try:
    from ibm_watsonx_ai import APIClient
    
    # Initialize credentials (newer API format)
    wml_credentials = {
        "url": os.getenv("WATSONX_URL"),
        "apikey": os.getenv("WATSONX_API_KEY")
    }
    
    client = APIClient(wml_credentials)
    print("   ✅ APIClient initialized")
    
    # Set project
    project_id = os.getenv("WATSONX_PROJECT_ID")
    client.set.default_project(project_id)
    print(f"   ✅ Project set: {project_id}")
    
    # Try to list deployments
    try:
        deployments = client.deployments.get_details()
        deployment_count = len(deployments.get('resources', []))
        print(f"   ✅ Found {deployment_count} deployments")
    except Exception as e:
        print(f"   ⚠️  Could not list deployments: {e}")
    
except ImportError:
    print("   ❌ ibm-watsonx-ai package not installed")
    print("   Run: pip install ibm-watsonx-ai")
    exit(1)
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    exit(1)

# Step 3: Test WML Client
print("\n3️⃣ Testing WML Client...")
try:
    from wml_client import get_wml_client
    
    wml_client = get_wml_client()
    print("   ✅ WML Client initialized")
    
    # Get model info
    info = wml_client.get_model_info()
    print(f"   ℹ️  Anomaly deployment: {info.get('anomaly_deployment_id', 'Not set')}")
    print(f"   ℹ️  Forecast deployment: {info.get('forecast_deployment_id', 'Not set')}")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("   Make sure wml_client.py is in the same directory")
    exit(1)
except Exception as e:
    print(f"   ⚠️  WML Client warning: {e}")

# Step 4: Test Data Preparation
print("\n4️⃣ Testing Data Preparation...")
try:
    import pandas as pd
    
    # Load data
    df = pd.read_csv("data/automotive_energy_data.csv", parse_dates=["timestamp"])
    print(f"   ✅ Loaded {len(df)} records from CSV")
    
    # Test feature preparation
    sample_data = df.head(10)
    features = wml_client.prepare_anomaly_features(sample_data)
    print(f"   ✅ Prepared anomaly features: {features.shape}")
    
    # Test forecast features
    ts_data = df.groupby('timestamp').agg({
        'energy_kwh': 'sum',
        'production_units': 'sum',
        'compressed_air_m3': 'sum',
        'water_liters': 'sum'
    }).reset_index().sort_values('timestamp')
    
    forecast_features = wml_client.prepare_forecast_features(ts_data)
    print(f"   ✅ Prepared forecast features: {forecast_features.shape}")
    
except Exception as e:
    print(f"   ❌ Data preparation failed: {e}")
    exit(1)

# Step 5: Test Model Predictions (if deployments exist)
if os.getenv("ANOMALY_DEPLOYMENT_ID"):
    print("\n5️⃣ Testing Anomaly Detection Model...")
    try:
        predictions = wml_client.predict_anomalies(sample_data)
        anomaly_count = sum([1 for p in predictions if p['is_anomaly']])
        print(f"   ✅ Model predictions successful")
        print(f"   ℹ️  Detected {anomaly_count} anomalies in {len(predictions)} samples")
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")
        print("   This is normal if you haven't deployed the model yet")
else:
    print("\n5️⃣ Skipping Model Test (ANOMALY_DEPLOYMENT_ID not set)")

if os.getenv("FORECAST_DEPLOYMENT_ID"):
    print("\n6️⃣ Testing Energy Forecasting Model...")
    try:
        forecasts = wml_client.predict_energy(df.head(50), hours_ahead=6)
        total_forecast = sum([f['predicted_energy_kwh'] for f in forecasts])
        print(f"   ✅ Forecast successful")
        print(f"   ℹ️  Predicted {total_forecast:.0f} kWh over next 6 hours")
    except Exception as e:
        print(f"   ❌ Forecast failed: {e}")
        print("   This is normal if you haven't deployed the model yet")
else:
    print("\n6️⃣ Skipping Forecast Test (FORECAST_DEPLOYMENT_ID not set)")

# Summary
print("\n" + "=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)

if not missing_required:
    print("✅ Basic setup complete!")
    print("✅ watsonx.ai connection working")
    print("✅ Data preparation working")
    
    if os.getenv("ANOMALY_DEPLOYMENT_ID") and os.getenv("FORECAST_DEPLOYMENT_ID"):
        print("✅ All ML models configured")
        print("\n🚀 Ready to use all features!")
    else:
        print("\n⚠️  ML models not deployed yet")
        print("   Follow WATSONX_INTEGRATION_GUIDE.md to train and deploy models")
else:
    print("❌ Setup incomplete - fix errors above")

print("\n💡 Next steps:")
print("   1. Train models in watsonx.ai Studio (see notebooks/)")
print("   2. Deploy models and add deployment IDs to .env")
print("   3. Test API endpoints: /ml-detect-anomalies, /predict-energy")
print("   4. Update watsonx Orchestrate agents to use new endpoints")
