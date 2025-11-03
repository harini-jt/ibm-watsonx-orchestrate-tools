"""
Prepare training data for watsonx.ai ML models
Creates datasets for:
1. Anomaly detection (Isolation Forest)
2. Energy forecasting (Time Series)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Load the automotive data
df = pd.read_csv("data/automotive_energy_data.csv", parse_dates=["timestamp"])

print("=" * 60)
print("📊 Preparing ML Training Data for watsonx.ai")
print("=" * 60)

# ========================================
# DATASET 1: ANOMALY DETECTION
# ========================================
print("\n1️⃣  Creating Anomaly Detection Dataset...")

# Create features for anomaly detection
anomaly_features = df.copy()

# Add time-based features
anomaly_features['hour'] = anomaly_features['timestamp'].dt.hour
anomaly_features['day_of_week'] = anomaly_features['timestamp'].dt.dayofweek
anomaly_features['is_night_shift'] = (anomaly_features['shift'] == 'SHIFT-C').astype(int)
anomaly_features['is_operational'] = (anomaly_features['status'] == 'OPERATIONAL').astype(int)

# Calculate derived features
anomaly_features['energy_per_unit'] = np.where(
    anomaly_features['production_units'] > 0,
    anomaly_features['energy_kwh'] / anomaly_features['production_units'],
    anomaly_features['energy_kwh']
)

anomaly_features['air_per_unit'] = np.where(
    anomaly_features['production_units'] > 0,
    anomaly_features['compressed_air_m3'] / anomaly_features['production_units'],
    anomaly_features['compressed_air_m3']
)

# Label anomalies (using our existing rule-based logic as ground truth)
def label_anomaly(row):
    """Label data as anomaly (1) or normal (0)"""
    
    # Paint oven idle
    if 'PAINT' in row['zone_id']:
        if row['production_units'] == 0 and row['energy_kwh'] > 3000:
            return 1
    
    # Compressed air leak
    if row['production_units'] <= 1 and row['compressed_air_m3'] > 1500:
        return 1
    
    # HVAC overcooling
    if row['temperature_c'] < 19 and row['production_units'] <= 1:
        return 1
    
    # Standby power waste
    if row['status'] == 'STANDBY' and row['energy_kwh'] > 500:
        return 1
    
    # Energy per vehicle high
    if row['production_units'] > 0:
        if row['energy_per_unit'] > 1200:
            return 1
    
    return 0

anomaly_features['is_anomaly'] = anomaly_features.apply(label_anomaly, axis=1)

# Select final features for training
ml_features = [
    'energy_kwh', 'production_units', 'compressed_air_m3', 
    'water_liters', 'temperature_c', 'efficiency_score',
    'hour', 'day_of_week', 'is_night_shift', 'is_operational',
    'energy_per_unit', 'air_per_unit', 'is_anomaly'
]

anomaly_dataset = anomaly_features[ml_features].copy()

# Encode zone_id separately (will handle in model)
anomaly_dataset['zone_encoded'] = pd.Categorical(anomaly_features['zone_id']).codes

# Save
os.makedirs('data/ml_training', exist_ok=True)
anomaly_dataset.to_csv('data/ml_training/anomaly_detection_dataset.csv', index=False)

print(f"   ✅ Created: data/ml_training/anomaly_detection_dataset.csv")
print(f"   📈 Total samples: {len(anomaly_dataset)}")
print(f"   🔴 Anomalies: {anomaly_dataset['is_anomaly'].sum()} ({anomaly_dataset['is_anomaly'].mean()*100:.1f}%)")
print(f"   🟢 Normal: {(anomaly_dataset['is_anomaly']==0).sum()} ({(1-anomaly_dataset['is_anomaly'].mean())*100:.1f}%)")

# ========================================
# DATASET 2: TIME SERIES FORECASTING
# ========================================
print("\n2️⃣  Creating Energy Forecasting Dataset...")

# Aggregate by timestamp for plant-level forecasting
ts_data = df.groupby('timestamp').agg({
    'energy_kwh': 'sum',
    'production_units': 'sum',
    'co2_kg': 'sum',
    'compressed_air_m3': 'sum',
    'water_liters': 'sum'
}).reset_index()

# Sort by time
ts_data = ts_data.sort_values('timestamp')

# Add time features
ts_data['hour'] = ts_data['timestamp'].dt.hour
ts_data['day_of_week'] = ts_data['timestamp'].dt.dayofweek
ts_data['is_weekend'] = ts_data['day_of_week'].isin([5, 6]).astype(int)

# Create lag features (for ML-based forecasting)
for lag in [1, 2, 3, 6, 12, 24]:
    ts_data[f'energy_lag_{lag}h'] = ts_data['energy_kwh'].shift(lag)
    ts_data[f'production_lag_{lag}h'] = ts_data['production_units'].shift(lag)

# Rolling statistics
ts_data['energy_rolling_mean_6h'] = ts_data['energy_kwh'].rolling(window=6, min_periods=1).mean()
ts_data['energy_rolling_std_6h'] = ts_data['energy_kwh'].rolling(window=6, min_periods=1).std()

# Drop NaN from lag features
ts_data = ts_data.dropna()

# Save
ts_data.to_csv('data/ml_training/energy_forecasting_dataset.csv', index=False)

print(f"   ✅ Created: data/ml_training/energy_forecasting_dataset.csv")
print(f"   📈 Total samples: {len(ts_data)}")
print(f"   📅 Date range: {ts_data['timestamp'].min()} to {ts_data['timestamp'].max()}")

# ========================================
# DATASET 3: ZONE-SPECIFIC FORECASTING
# ========================================
print("\n3️⃣  Creating Zone-Specific Datasets...")

for zone in df['zone_id'].unique():
    zone_data = df[df['zone_id'] == zone].copy()
    zone_data = zone_data.sort_values('timestamp')
    
    # Add time features
    zone_data['hour'] = zone_data['timestamp'].dt.hour
    zone_data['day_of_week'] = zone_data['timestamp'].dt.dayofweek
    
    # Lag features
    for lag in [1, 2, 3, 6]:
        zone_data[f'energy_lag_{lag}h'] = zone_data['energy_kwh'].shift(lag)
    
    zone_data = zone_data.dropna()
    
    # Save
    zone_name = zone.replace('ZONE-', '').lower()
    zone_data.to_csv(f'data/ml_training/forecast_{zone_name}.csv', index=False)
    print(f"   ✅ Created: forecast_{zone_name}.csv ({len(zone_data)} samples)")

# ========================================
# SUMMARY STATISTICS
# ========================================
print("\n" + "=" * 60)
print("📊 Dataset Summary")
print("=" * 60)
print(f"\n🎯 Anomaly Detection Dataset:")
print(anomaly_dataset.describe())

print(f"\n📈 Energy Forecasting Dataset (first 5 rows):")
print(ts_data.head())

print("\n" + "=" * 60)
print("✅ Data preparation complete!")
print("=" * 60)
print("\n📂 Files created in data/ml_training/:")
print("   • anomaly_detection_dataset.csv")
print("   • energy_forecasting_dataset.csv")
print("   • forecast_*.csv (per zone)")
print("\n🚀 Next step: Upload these to watsonx.ai Studio")
