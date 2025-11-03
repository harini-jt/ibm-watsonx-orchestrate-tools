"""
watsonx.ai ML Client for GreenOps
Handles interactions with deployed ML models
"""

from ibm_watsonx_ai import APIClient
import os
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class WatsonxMLClient:
    """Client for watsonx.ai model inference"""
    
    def __init__(self):
        """Initialize watsonx.ai client with credentials"""
        api_key = os.getenv("WATSONX_API_KEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        space_id = os.getenv("WATSONX_SPACE_ID")
        url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        
        if not api_key:
            raise ValueError(
                "Missing watsonx.ai credentials. "
                "Set WATSONX_API_KEY in .env file"
            )
        
        # Initialize credentials (newer API format)
        wml_credentials = {
            "url": url,
            "apikey": api_key
        }
        
        # Initialize client
        self.client = APIClient(wml_credentials)
        
        # Use space for deployments, project for training
        if space_id:
            self.client.set.default_space(space_id)
        elif project_id:
            self.client.set.default_project(project_id)
        else:
            raise ValueError(
                "Must set either WATSONX_SPACE_ID or WATSONX_PROJECT_ID in .env file"
            )
        
        # Deployment IDs
        self.anomaly_deployment_id = os.getenv("ANOMALY_DEPLOYMENT_ID")
        self.forecast_deployment_id = os.getenv("FORECAST_DEPLOYMENT_ID")
        
        # Feature names (must match training data)
        self.anomaly_features = [
            'energy_kwh', 'production_units', 'compressed_air_m3', 
            'water_liters', 'temperature_c', 'efficiency_score',
            'hour', 'day_of_week', 'is_night_shift', 'is_operational',
            'energy_per_unit', 'air_per_unit', 'zone_encoded'
        ]
        
        self.forecast_features = [
            'energy_kwh', 'production_units', 'co2_kg', 'compressed_air_m3', 
            'water_liters', 'hour', 'day_of_week', 'is_weekend', 
            'energy_lag_1h', 'production_lag_1h'
        ]
        
        print("✅ WatsonxMLClient initialized successfully")
    
    def prepare_anomaly_features(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for anomaly detection model
        
        Args:
            data_df: DataFrame with operational data
            
        Returns:
            DataFrame with model-ready features
        """
        df = data_df.copy()
        
        # Add time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_night_shift'] = (df['shift'] == 'SHIFT-C').astype(int)
        df['is_operational'] = (df['status'] == 'OPERATIONAL').astype(int)
        
        # Calculate derived features
        df['energy_per_unit'] = np.where(
            df['production_units'] > 0,
            df['energy_kwh'] / df['production_units'],
            df['energy_kwh']
        )
        
        df['air_per_unit'] = np.where(
            df['production_units'] > 0,
            df['compressed_air_m3'] / df['production_units'],
            df['compressed_air_m3']
        )
        
        # Encode zone_id
        df['zone_encoded'] = pd.Categorical(df['zone_id']).codes
        
        return df[self.anomaly_features]
    
    def prepare_forecast_features(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for energy forecasting model
        
        Args:
            data_df: DataFrame with aggregated time series data
            
        Returns:
            DataFrame with model-ready features
        """
        df = data_df.copy()
        
        # Add time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Calculate CO2 if not present (assuming energy-based calculation)
        if 'co2_kg' not in df.columns:
            # Average emission factor: ~0.82 kg CO2 per kWh (can adjust based on region)
            df['co2_kg'] = df['energy_kwh'] * 0.82
        
        # Create lag features (only 1h for production and energy)
        df['energy_lag_1h'] = df['energy_kwh'].shift(1)
        df['production_lag_1h'] = df['production_units'].shift(1)
        
        # Drop NaN from lag features
        df = df.dropna()
        
        # Return only the features the model expects
        return df[self.forecast_features]
    
    def predict_anomalies(self, data_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalies using ML model
        
        Args:
            data_df: DataFrame with operational data
            
        Returns:
            List of anomaly predictions with scores
        """
        if not self.anomaly_deployment_id:
            raise ValueError("ANOMALY_DEPLOYMENT_ID not set in .env")
        
        # Prepare features
        features_df = self.prepare_anomaly_features(data_df)
        
        # Prepare payload for watsonx.ai
        payload = {
            "input_data": [{
                "fields": self.anomaly_features,
                "values": features_df.values.tolist()
            }]
        }
        
        # Get predictions
        try:
            response = self.client.deployments.score(
                self.anomaly_deployment_id, 
                payload
            )
            
            # DEBUG: Print first prediction to understand format
            predictions = response['predictions'][0]
            print(f"DEBUG - Prediction keys: {predictions.keys()}")
            print(f"DEBUG - First 3 predictions: {predictions['values'][:3]}")
            if 'fields' in predictions:
                print(f"DEBUG - Fields: {predictions['fields']}")
            
            # Parse response - AutoAI format
            pred_values = predictions['values']
            pred_fields = predictions.get('fields', [])
            
            # Combine with original data
            results = []
            for idx, pred_row in enumerate(pred_values):
                row = data_df.iloc[idx]
                
                # AutoAI format: [prediction, [probability_0, probability_1]]
                # Example: [0.0, [0.996, 0.004]] means class 0 with 99.6% confidence
                if isinstance(pred_row, list) and len(pred_row) >= 2:
                    prediction = pred_row[0]  # 0.0 or 1.0
                    
                    # Extract probabilities
                    if isinstance(pred_row[1], list) and len(pred_row[1]) >= 2:
                        prob_class_0 = pred_row[1][0]  # Probability of normal (class 0)
                        prob_class_1 = pred_row[1][1]  # Probability of anomaly (class 1)
                        anomaly_score = prob_class_1
                    else:
                        anomaly_score = 0.5
                else:
                    prediction = pred_row if not isinstance(pred_row, list) else pred_row[0]
                    anomaly_score = 0.5
                
                results.append({
                    'timestamp': row['timestamp'].isoformat(),
                    'zone_id': row['zone_id'],
                    'is_anomaly': bool(prediction == 1.0),  # 1.0 = anomaly, 0.0 = normal
                    'anomaly_score': float(anomaly_score),  # Probability of anomaly
                    'energy_kwh': float(row['energy_kwh']),
                    'production_units': int(row['production_units']),
                    'shift': row['shift'],
                    'status': row['status']
                })
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Anomaly prediction failed: {str(e)}")
    
    def predict_energy(
        self, 
        historical_data: pd.DataFrame, 
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Forecast energy consumption for next N hours
        
        Args:
            historical_data: DataFrame with aggregated historical data
            hours_ahead: Number of hours to forecast
            
        Returns:
            List of energy forecasts
        """
        if not self.forecast_deployment_id:
            raise ValueError("FORECAST_DEPLOYMENT_ID not set in .env")
        
        # Aggregate data by timestamp
        ts_data = historical_data.groupby('timestamp').agg({
            'energy_kwh': 'sum',
            'production_units': 'sum',
            'compressed_air_m3': 'sum',
            'water_liters': 'sum'
        }).reset_index().sort_values('timestamp')
        
        # Prepare features
        features_df = self.prepare_forecast_features(ts_data)
        
        if len(features_df) == 0:
            raise ValueError("Not enough historical data for forecasting")
        
        # Get last row for recursive forecasting
        last_row = features_df.iloc[-1].copy()
        last_energy = last_row['energy_kwh']
        last_production = last_row['production_units']
        forecasts = []
        
        for hour in range(1, hours_ahead + 1):
            # Update time features for this future hour
            future_timestamp = ts_data['timestamp'].iloc[-1] + pd.Timedelta(hours=hour)
            last_row['hour'] = future_timestamp.hour
            last_row['day_of_week'] = future_timestamp.dayofweek
            last_row['is_weekend'] = 1 if future_timestamp.dayofweek in [5, 6] else 0
            
            # Update lag features with the last prediction
            # For recursive forecasting: use previous prediction as lag_1h
            last_row['energy_lag_1h'] = last_energy
            last_row['production_lag_1h'] = last_production
            
            # Prepare features
            future_features = last_row[self.forecast_features].values.reshape(1, -1)
            
            payload = {
                "input_data": [{
                    "fields": self.forecast_features,
                    "values": future_features.tolist()
                }]
            }
            
            try:
                response = self.client.deployments.score(
                    self.forecast_deployment_id,
                    payload
                )
                
                # DEBUG: Print response format on first iteration
                if hour == 1:
                    print(f"DEBUG FORECAST - Response keys: {response['predictions'][0].keys()}")
                    print(f"DEBUG FORECAST - First prediction: {response['predictions'][0]['values'][0]}")
                
                # AutoAI time series returns: [[predicted_value]]
                pred_row = response['predictions'][0]['values'][0]
                if isinstance(pred_row, list) and len(pred_row) > 0:
                    # Double nested: [[value]] -> extract inner list first
                    if isinstance(pred_row[0], list):
                        predicted_energy = pred_row[0][0]
                    else:
                        predicted_energy = pred_row[0]
                else:
                    predicted_energy = pred_row
                
                # Update last values for next iteration
                last_energy = predicted_energy
                # Assume production stays similar (or use a production forecast model)
                last_production = last_row['production_units']
                
                # Update other features that depend on energy
                last_row['energy_kwh'] = predicted_energy
                last_row['co2_kg'] = predicted_energy * 0.82
                
                forecasts.append({
                    'hour_ahead': hour,
                    'predicted_energy_kwh': round(float(predicted_energy), 2),
                    'timestamp': future_timestamp.isoformat()
                })
                
            except Exception as e:
                raise RuntimeError(f"Energy forecast failed at hour {hour}: {str(e)}")
        
        return forecasts
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about deployed models"""
        info = {
            'anomaly_deployment_id': self.anomaly_deployment_id,
            'forecast_deployment_id': self.forecast_deployment_id,
            'anomaly_features': self.anomaly_features,
            'forecast_features': self.forecast_features
        }
        
        # Try to get deployment details
        try:
            if self.anomaly_deployment_id:
                anomaly_details = self.client.deployments.get_details(
                    self.anomaly_deployment_id
                )
                info['anomaly_status'] = anomaly_details.get('entity', {}).get('status', {}).get('state')
        except:
            info['anomaly_status'] = 'unknown'
        
        try:
            if self.forecast_deployment_id:
                forecast_details = self.client.deployments.get_details(
                    self.forecast_deployment_id
                )
                info['forecast_status'] = forecast_details.get('entity', {}).get('status', {}).get('state')
        except:
            info['forecast_status'] = 'unknown'
        
        return info


# Singleton instance
_wml_client = None

def get_wml_client() -> WatsonxMLClient:
    """Get or create WatsonxMLClient singleton"""
    global _wml_client
    if _wml_client is None:
        _wml_client = WatsonxMLClient()
    return _wml_client
