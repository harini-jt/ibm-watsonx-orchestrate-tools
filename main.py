from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
import os
import numpy as np
from datetime import datetime

# Try to import watsonx.ai client (optional for ML features)
try:
    from wml_client import get_wml_client
    WML_AVAILABLE = True
except Exception as e:
    WML_AVAILABLE = False
    print(f"⚠️ watsonx.ai integration not available: {e}")

app = FastAPI(
    title=" Automotive Plant Sustainability APIs",
    version="2.0.0",
    description="Automotive plant sustainability APIs with watsonx.ai ML models",
    servers=[
        {"url": "https://ibm-watsonx-orchestrate-tools.vercel.app/", "description": "Production Server"},
        {"url": "http://127.0.0.1:8000", "description": "Local Development Server"}
    ],
)

# Add CORS middleware to allow browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Configuration for GreenOps analysis
CONFIG = {
    "ENERGY_PER_VEHICLE_BENCHMARK": 1200.0,   # kWh per vehicle
    "PAINT_OVEN_IDLE_MULTIPLIER": 1.2,
    "AIR_LEAK_RATIO_THRESHOLD": 1.25,
    "HVAC_LOW_TEMP_THRESHOLD": 19.0,         # °C
    "STANDBY_ENERGY_PERCENT": 0.15,          # 15% of normal when standby
    "CO2_FACTOR": 0.82,                      # kg CO2 per kWh
    "CURRENCY_PER_KWH": 0.07,                # ₹ per kWh
    "HOURS_DAY": 24
}

# Pydantic Models for API responses
class ZoneEnergyModel(BaseModel):
    zone_id: str
    zone_energy_kwh: float
    zone_energy_share_percent: float = Field(alias="zone_energy_share_%")

class KPIModel(BaseModel):
    total_energy_kwh: float
    total_co2_kg: float
    total_vehicles: int
    energy_per_vehicle_kwh: Optional[float]
    co2_per_vehicle_kg: Optional[float]
    zone_energy: List[ZoneEnergyModel]

class AnomalyModel(BaseModel):
    type: str
    zone: Optional[str] = None
    timestamp: str
    energy_kwh: Optional[float] = None
    production_units: Optional[int] = None
    compressed_air_m3: Optional[float] = None
    temperature_c: Optional[float] = None
    operational_median: Optional[float] = None
    energy_per_vehicle_kwh: Optional[float] = None
    benchmark_kwh: Optional[float] = None
    note: str

class ActionModel(BaseModel):
    id: str
    priority: str
    title: str
    zone: str
    expected_savings_kwh_per_hour: Optional[float] = None
    expected_savings_co2_kg_per_hour: Optional[float] = None
    expected_savings_currency_per_hour: Optional[float] = None
    expected_savings_kwh_per_period: Optional[float] = None
    expected_savings_co2_kg_per_period: Optional[float] = None
    expected_savings_currency_per_period: Optional[float] = None
    implementation: str
    related_anomaly: AnomalyModel

class ReportModel(BaseModel):
    kpis: KPIModel
    anomalies: List[AnomalyModel]
    actions: List[ActionModel]
    generated_at: str

class ConfigModel(BaseModel):
    ENERGY_PER_VEHICLE_BENCHMARK: float
    PAINT_OVEN_IDLE_MULTIPLIER: float
    AIR_LEAK_RATIO_THRESHOLD: float
    HVAC_LOW_TEMP_THRESHOLD: float
    STANDBY_ENERGY_PERCENT: float
    CO2_FACTOR: float
    CURRENCY_PER_KWH: float
    HOURS_DAY: int
# # --- 3. Load Environment Variable ---
# API_KEY = os.getenv("API_KEY") 
# if not API_KEY:
#     raise RuntimeError("Environment variable 'API_KEY' not set.")
# Load CSV once at startup
DATA_PATH = "data/automotive_energy_data.csv"
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

# Helper Functions from GreenOps Agents

def validate_and_clean_data(data_df):
    """Validate and clean data similar to fetch_data in greenops_agents.py"""
    # Basic validation
    expected_cols = {"timestamp", "zone_id", "energy_kwh", "co2_kg", "production_units", 
                    "compressed_air_m3", "water_liters", "temperature_c", "shift", 
                    "efficiency_score", "status"}
    if not expected_cols.issubset(set(data_df.columns)):
        raise ValueError(f"CSV missing expected columns. Found: {data_df.columns.tolist()}")
    
    # Fill NA values
    data_df = data_df.fillna({
        "production_units": 0, 
        "compressed_air_m3": 0, 
        "water_liters": 0, 
        "temperature_c": np.nan
    })
    
    # Ensure numeric types
    numeric_cols = ["energy_kwh", "co2_kg", "production_units", "compressed_air_m3", 
                   "water_liters", "temperature_c"]
    for col in numeric_cols:
        data_df[col] = pd.to_numeric(data_df[col], errors="coerce").fillna(0)
    
    return data_df

def compute_kpis(data_df):
    """Compute KPIs from the data"""
    total_energy = data_df["energy_kwh"].sum()
    total_co2 = data_df["co2_kg"].sum()
    total_vehicles = data_df["production_units"].sum()
    energy_per_vehicle = total_energy / total_vehicles if total_vehicles > 0 else float("inf")
    co2_per_vehicle = total_co2 / total_vehicles if total_vehicles > 0 else float("inf")
    
    zone_energy = data_df.groupby("zone_id")["energy_kwh"].sum().reset_index().rename(
        columns={"energy_kwh": "zone_energy_kwh"}
    )
    zone_energy["zone_energy_share_%"] = (zone_energy["zone_energy_kwh"] / total_energy * 100).round(2)
    
    kpis = {
        "total_energy_kwh": round(float(total_energy), 2),
        "total_co2_kg": round(float(total_co2), 2),
        "total_vehicles": int(total_vehicles),
        "energy_per_vehicle_kwh": round(float(energy_per_vehicle), 2) if total_vehicles > 0 else None,
        "co2_per_vehicle_kg": round(float(co2_per_vehicle), 2) if total_vehicles > 0 else None,
        "zone_energy": zone_energy.to_dict(orient="records")
    }
    return kpis

def detect_anomalies(data_df):
    """Detect anomalies in plant operations"""
    anomalies = []
    cfg = CONFIG
    
    # 1) Paint oven idle: energy high while production = 0 in paint shop
    paint_df = data_df[data_df["zone_id"].str.contains("PAINT", case=False)]
    if len(paint_df) > 0:
        # baseline: median energy when production > 0
        baseline_paint = paint_df[paint_df["production_units"] > 0]["energy_kwh"].median() or 1.0
        # find rows where production==0 but energy > baseline * multiplier
        paint_idle = paint_df[
            (paint_df["production_units"] == 0) & 
            (paint_df["energy_kwh"] > baseline_paint * cfg["PAINT_OVEN_IDLE_MULTIPLIER"])
        ]
        for _, r in paint_idle.iterrows():
            anomalies.append({
                "type": "PAINT_OVEN_IDLE",
                "zone": r["zone_id"],
                "timestamp": r["timestamp"].isoformat(),
                "energy_kwh": float(r["energy_kwh"]),
                "production_units": int(r["production_units"]),
                "note": f"High paint energy ({r['energy_kwh']} kWh) while production=0 (baseline {baseline_paint:.1f} kWh)."
            })

    # 2) Compressed air leak: high air usage but very low or zero production (by zone)
    air_zones = data_df[data_df["compressed_air_m3"] > 0].groupby("zone_id")
    for zone, group in air_zones:
        # baseline production-weighted median or mean
        baseline_air = group[group["production_units"] > 0]["compressed_air_m3"].median() or 1.0
        # consider hours where production is <= 1 and compressed_air > threshold*baseline
        suspect = group[
            (group["production_units"] <= 1) & 
            (group["compressed_air_m3"] > baseline_air * cfg["AIR_LEAK_RATIO_THRESHOLD"])
        ]
        for _, r in suspect.iterrows():
            anomalies.append({
                "type": "COMPRESSED_AIR_LEAK",
                "zone": zone,
                "timestamp": r["timestamp"].isoformat(),
                "compressed_air_m3": float(r["compressed_air_m3"]),
                "production_units": int(r["production_units"]),
                "note": f"High compressed air ({r['compressed_air_m3']} m3) with little/no production (baseline {baseline_air:.1f} m3)."
            })

    # 3) HVAC overcooling: temperature below threshold while production low/none
    hvac_df = data_df[data_df["zone_id"].str.contains("HVAC|UTILITIES|BATTERY|ASSEMBLY|BODY|CASTING|PAINT", case=False)]
    hvac_suspects = hvac_df[
        (hvac_df["temperature_c"] < cfg["HVAC_LOW_TEMP_THRESHOLD"]) & 
        (hvac_df["production_units"] <= 1)
    ]
    for _, r in hvac_suspects.iterrows():
        anomalies.append({
            "type": "HVAC_OVERCOOLING",
            "zone": r["zone_id"],
            "timestamp": r["timestamp"].isoformat(),
            "temperature_c": float(r["temperature_c"]),
            "note": f"Low temp {r['temperature_c']}°C with production {r['production_units']}."
        })

    # 4) Standby / phantom power: zone consuming a notable fraction while status is STANDBY or production==0
    standby = data_df[
        (data_df["status"].str.upper() == "STANDBY") | 
        (data_df["production_units"] == 0)
    ]
    # compare to zone typical consumption when operational
    for zone, group in standby.groupby("zone_id"):
        oper_median = data_df[
            (data_df["zone_id"] == zone) & 
            (data_df["status"].str.upper() == "OPERATIONAL")
        ]["energy_kwh"].median() or 1.0
        
        for _, r in group.iterrows():
            if r["energy_kwh"] > oper_median * cfg["STANDBY_ENERGY_PERCENT"]:
                anomalies.append({
                    "type": "STANDBY_POWER_WASTE",
                    "zone": zone,
                    "timestamp": r["timestamp"].isoformat(),
                    "energy_kwh": float(r["energy_kwh"]),
                    "operational_median": float(oper_median),
                    "note": f"Standby energy {r['energy_kwh']}kWh is > {cfg['STANDBY_ENERGY_PERCENT']*100}% of operational median ({oper_median:.1f} kWh)."
                })

    # 5) Plant-level energy per vehicle exceed benchmark
    kpis = compute_kpis(data_df)
    if kpis["total_vehicles"] > 0 and kpis["energy_per_vehicle_kwh"] and kpis["energy_per_vehicle_kwh"] > cfg["ENERGY_PER_VEHICLE_BENCHMARK"]:
        anomalies.append({
            "type": "ENERGY_PER_VEHICLE_HIGH",
            "timestamp": datetime.utcnow().isoformat(),
            "energy_per_vehicle_kwh": kpis["energy_per_vehicle_kwh"],
            "benchmark_kwh": cfg["ENERGY_PER_VEHICLE_BENCHMARK"],
            "note": f"Plant energy per vehicle {kpis['energy_per_vehicle_kwh']}kWh > benchmark {cfg['ENERGY_PER_VEHICLE_BENCHMARK']}kWh."
        })

    return anomalies

def plan_actions(anomalies, data_df):
    """Map anomalies to actions with estimated savings and CO2 reductions."""
    cfg = CONFIG
    actions = []
    
    # loop anomalies and generate action entries
    for a in anomalies:
        if a["type"] == "PAINT_OVEN_IDLE":
            # estimate savings: assume auto-shutdown reduces energy by the measured energy for that hour
            saved_kwh = a["energy_kwh"]
            saved_co2 = saved_kwh * cfg["CO2_FACTOR"]
            saved_cost = saved_kwh * cfg["CURRENCY_PER_KWH"]
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "HIGH",
                "title": f"Auto-shutdown or reduce temp for {a['zone']}",
                "zone": a["zone"],
                "expected_savings_kwh_per_hour": round(saved_kwh, 2),
                "expected_savings_co2_kg_per_hour": round(saved_co2, 2),
                "expected_savings_currency_per_hour": round(saved_cost, 2),
                "implementation": "Update PLC schedule or add auto-shutdown rule after production ends",
                "related_anomaly": a
            })
        elif a["type"] == "COMPRESSED_AIR_LEAK":
            # estimate air savings: use measured compressed air and convert roughly to energy
            # assume 0.1 kWh per m3 (approximate conversion placeholder)
            m3 = a["compressed_air_m3"]
            saved_kwh = m3 * 0.1
            saved_co2 = saved_kwh * cfg["CO2_FACTOR"]
            saved_cost = saved_kwh * cfg["CURRENCY_PER_KWH"]
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "HIGH",
                "title": f"Inspect compressed air lines in {a['zone']}",
                "zone": a["zone"],
                "expected_savings_kwh_per_hour": round(saved_kwh, 2),
                "expected_savings_co2_kg_per_hour": round(saved_co2, 2),
                "expected_savings_currency_per_hour": round(saved_cost, 2),
                "implementation": "Schedule maintenance, pressure test and seal leaks",
                "related_anomaly": a
            })
        elif a["type"] == "HVAC_OVERCOOLING":
            # estimate savings by raising temp by 2-3°C: rough percent reduction
            est_kwh = 100.0  # placeholder per hour
            saved_kwh = est_kwh * 0.25  # assume 25% saving by adjustment
            saved_co2 = saved_kwh * cfg["CO2_FACTOR"]
            saved_cost = saved_kwh * cfg["CURRENCY_PER_KWH"]
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "MEDIUM",
                "title": f"Adjust HVAC setpoint in {a['zone']} to reduce overcooling",
                "zone": a["zone"],
                "expected_savings_kwh_per_hour": round(saved_kwh, 2),
                "expected_savings_co2_kg_per_hour": round(saved_co2, 2),
                "expected_savings_currency_per_hour": round(saved_cost, 2),
                "implementation": "Raise setpoint by 2-3°C and optimize schedules",
                "related_anomaly": a
            })
        elif a["type"] == "STANDBY_POWER_WASTE":
            # estimate savings: difference between standby energy and allowable standby (15% of operational median)
            oper_med = a.get("operational_median", 0.0)
            allowable = oper_med * cfg["STANDBY_ENERGY_PERCENT"]
            waste = max(0.0, a["energy_kwh"] - allowable)
            saved_kwh = waste
            saved_co2 = saved_kwh * cfg["CO2_FACTOR"]
            saved_cost = saved_kwh * cfg["CURRENCY_PER_KWH"]
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "LOW",
                "title": f"Reduce standby power in {a['zone']}",
                "zone": a["zone"],
                "expected_savings_kwh_per_hour": round(saved_kwh, 2),
                "expected_savings_co2_kg_per_hour": round(saved_co2, 2),
                "expected_savings_currency_per_hour": round(saved_cost, 2),
                "implementation": "Enable deep-sleep, change PLC, or turn off non-critical drives",
                "related_anomaly": a
            })
        elif a["type"] == "ENERGY_PER_VEHICLE_HIGH":
            # provide high-level recommendation
            total_excess = (a["energy_per_vehicle_kwh"] - a["benchmark_kwh"]) * data_df["production_units"].sum()
            saved_co2 = total_excess * cfg["CO2_FACTOR"]
            saved_cost = total_excess * cfg["CURRENCY_PER_KWH"]
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "HIGH",
                "title": "Plant-level energy optimization program",
                "zone": "PLANT",
                "expected_savings_kwh_per_period": round(total_excess, 2),
                "expected_savings_co2_kg_per_period": round(saved_co2, 2),
                "expected_savings_currency_per_period": round(saved_cost, 2),
                "implementation": "Cross-zone program: schedule optimization, workforce training, maintenance program",
                "related_anomaly": a
            })
        else:
            actions.append({
                "id": f"ACT-{len(actions)+1}",
                "priority": "LOW",
                "title": f"Investigate {a.get('type')}",
                "zone": a.get("zone", "UNKNOWN"),
                "implementation": "Manual follow-up",
                "related_anomaly": a
            })
    return actions

def generate_report(kpis, anomalies, actions):
    """Generate sustainability report"""
    # Text summary (console-friendly)
    lines = []
    lines.append("═══════════════════════════════════════════")
    lines.append("  🚗 AUTOMOTIVE PLANT SUSTAINABILITY REPORT")
    lines.append(f"  Date: {datetime.utcnow().date().isoformat()}")
    lines.append("═══════════════════════════════════════════")
    lines.append("")
    lines.append("📊 PRODUCTION METRICS:")
    lines.append(f"   • Vehicles Produced: {kpis['total_vehicles']}")
    lines.append(f"   • Energy Consumed: {kpis['total_energy_kwh']:,} kWh")
    lines.append(f"   • Energy per Vehicle: {kpis['energy_per_vehicle_kwh']} kWh")
    lines.append(f"   • CO₂ Emitted: {kpis['total_co2_kg']:,} kg")
    lines.append(f"   • CO₂ per Vehicle: {kpis['co2_per_vehicle_kg']} kg")
    lines.append("")
    lines.append("⚡ ENERGY CONSUMPTION BY ZONE:")
    for z in kpis["zone_energy"]:
        lines.append(f"   • {z['zone_id']}: {z['zone_energy_kwh']:,} kWh ({z['zone_energy_share_%']}%)")
    lines.append("")
    lines.append("🔴 ANOMALIES DETECTED:")
    if not anomalies:
        lines.append("   None")
    else:
        for idx, a in enumerate(anomalies, 1):
            lines.append(f"{idx}. {a['type']} - {a.get('zone', 'N/A')} - {a.get('note', '')}")
    lines.append("")
    lines.append("✅ RECOMMENDED ACTIONS:")
    for act in actions:
        lines.append(f" - [{act['priority']}] {act['title']} (Zone: {act['zone']})")
        # show savings if present
        if "expected_savings_kwh_per_hour" in act:
            lines.append(f"    Estimated savings: {act['expected_savings_kwh_per_hour']} kWh / hr, CO2 {act['expected_savings_co2_kg_per_hour']} kg / hr, Cost ₹{act['expected_savings_currency_per_hour']} / hr")
    lines.append("")
    lines.append("🌱 SDG9 ALIGNMENT: Industry innovation + sustainable infrastructure")
    report_text = "\n".join(lines)
    
    # Also produce JSON
    report_json = {
        "kpis": kpis,
        "anomalies": anomalies,
        "actions": actions,
        "generated_at": datetime.utcnow().isoformat()
    }
    return report_text, report_json

@app.get("/fetch_data")
def fetch_data(
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    data = df.copy()

    if zone_id:
        data = data[data["zone_id"] == zone_id]
    if shift:
        data = data[data["shift"] == shift]
    if status:
        data = data[data["status"] == status]
    if start_date:
        data = data[data["timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        data = data[data["timestamp"] <= pd.to_datetime(end_date)]

    # Convert Timestamp to string before returning
    data["timestamp"] = data["timestamp"].astype(str)

    result = data.to_dict(orient="records")
    return JSONResponse(content={"count": len(result), "data": result})


@app.get("/compute-kpis", response_model=KPIModel)
def compute_kpis_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    """Compute KPIs (Key Performance Indicators) for energy efficiency and production metrics."""
    try:
        # Apply same filters as fetch_data
        data = df.copy()
        
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if status:
            data = data[data["status"] == status]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found for the specified filters")
        
        # Validate and clean data
        data = validate_and_clean_data(data)
        
        # Compute KPIs
        kpis = compute_kpis(data)
        
        return KPIModel(**kpis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing KPIs: {str(e)}")


@app.get("/detect-anomalies")
def detect_anomalies_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    """Detect anomalies and inefficiencies in plant operations."""
    try:
        # Apply same filters as fetch_data
        data = df.copy()
        
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if status:
            data = data[data["status"] == status]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found for the specified filters")
        
        # Validate and clean data
        data = validate_and_clean_data(data)
        
        # Detect anomalies
        anomalies = detect_anomalies(data)
        
        return JSONResponse(content={
            "count": len(anomalies),
            "anomalies": anomalies
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@app.get("/plan-actions")
def plan_actions_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    """Generate actionable recommendations based on detected anomalies."""
    try:
        # Apply same filters as fetch_data
        data = df.copy()
        
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if status:
            data = data[data["status"] == status]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found for the specified filters")
        
        # Validate and clean data
        data = validate_and_clean_data(data)
        
        # Detect anomalies first
        anomalies = detect_anomalies(data)
        
        # Plan actions based on anomalies
        actions = plan_actions(anomalies, data)
        
        return JSONResponse(content={
            "count": len(actions),
            "actions": actions
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error planning actions: {str(e)}")


@app.get("/generate-report")
def generate_report_endpoint(
    format_type: str = Query("json", description="Response format: 'json' or 'text'"),
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    """Generate a comprehensive sustainability report."""
    try:
        # Apply same filters as fetch_data
        data = df.copy()
        
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if status:
            data = data[data["status"] == status]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found for the specified filters")
        
        # Validate and clean data
        data = validate_and_clean_data(data)
        
        # Run the pipeline
        kpis = compute_kpis(data)
        anomalies = detect_anomalies(data)
        actions = plan_actions(anomalies, data)
        report_text, report_json = generate_report(kpis, anomalies, actions)
        
        if format_type.lower() == "text":
            return JSONResponse(content={"report": report_text})
        else:
            return JSONResponse(content=report_json)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.get("/run-pipeline", response_model=ReportModel)
def run_pipeline_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: Optional[str] = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
):
    """Run the complete GreenOps pipeline: analyze data, detect anomalies, plan actions, and generate report."""
    try:
        # Apply same filters as fetch_data
        data = df.copy()
        
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if status:
            data = data[data["status"] == status]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found for the specified filters")
        
        # Validate and clean data
        data = validate_and_clean_data(data)
        
        # Run the complete pipeline
        kpis = compute_kpis(data)
        anomalies = detect_anomalies(data)
        actions = plan_actions(anomalies, data)
        _, report_json = generate_report(kpis, anomalies, actions)
        
        return ReportModel(**report_json)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running pipeline: {str(e)}")


@app.get("/config", response_model=ConfigModel)
def get_config():
    """Get current analysis configuration thresholds and parameters."""
    return ConfigModel(**CONFIG)


@app.put("/config", response_model=ConfigModel)
def update_config(config_update: ConfigModel):
    """Update analysis configuration thresholds and parameters."""
    global CONFIG
    try:
        CONFIG.update(config_update.dict())
        return ConfigModel(**CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


# ========================================
# ML-POWERED ENDPOINTS (watsonx.ai)
# ========================================

@app.get("/ml-detect-anomalies")
def ml_detect_anomalies_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone"),
    shift: Optional[str] = Query(None, description="Filter by shift"),
    start_date: Optional[str] = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End timestamp (YYYY-MM-DD)"),
    threshold: float = Query(0.5, description="Anomaly score threshold (0-1)")
):
    """
    🤖 ML-POWERED: Detect anomalies using watsonx.ai Isolation Forest model.
    Returns anomalies with confidence scores.
    """
    if not WML_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="watsonx.ai integration not configured. Set credentials in .env file."
        )
    
    try:
        # Apply filters
        data = df.copy()
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Get ML predictions
        wml_client = get_wml_client()
        predictions = wml_client.predict_anomalies(data)
        
        # Filter by threshold
        anomalies = [p for p in predictions if p['anomaly_score'] >= threshold]
        
        return JSONResponse(content={
            "count": len(anomalies),
            "total_samples": len(predictions),
            "anomaly_rate": round(len(anomalies) / len(predictions) * 100, 2),
            "threshold": threshold,
            "model_type": "watsonx.ai Isolation Forest",
            "anomalies": anomalies
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML anomaly detection failed: {str(e)}")


@app.get("/predict-energy")
def predict_energy_endpoint(
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours to forecast (1-168)"),
    zone_id: Optional[str] = Query(None, description="Zone to forecast (omit for plant-level)")
):
    """
    🤖 ML-POWERED: Forecast energy consumption using watsonx.ai XGBoost model.
    Predicts next 1-168 hours of energy usage.
    """
    if not WML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="watsonx.ai integration not configured"
        )
    
    try:
        data = df.copy()
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        
        # Get forecasts
        wml_client = get_wml_client()
        forecasts = wml_client.predict_energy(data, hours_ahead=hours_ahead)
        
        # Calculate summary stats
        total_predicted = sum([f['predicted_energy_kwh'] for f in forecasts])
        avg_per_hour = total_predicted / hours_ahead
        
        return JSONResponse(content={
            "zone": zone_id or "PLANT-LEVEL",
            "hours_ahead": hours_ahead,
            "total_predicted_kwh": round(total_predicted, 2),
            "average_per_hour_kwh": round(avg_per_hour, 2),
            "model_type": "watsonx.ai XGBoost",
            "forecasts": forecasts
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Energy forecasting failed: {str(e)}")


@app.get("/compare-detectors")
def compare_detectors_endpoint(
    zone_id: Optional[str] = Query(None, description="Filter by zone"),
    shift: Optional[str] = Query(None, description="Filter by shift")
):
    """
    📊 Compare rule-based vs ML-based anomaly detection.
    Shows differences between traditional and AI approaches.
    """
    if not WML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="watsonx.ai integration not configured"
        )
    
    try:
        # Apply filters
        data = df.copy()
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if shift:
            data = data[data["shift"] == shift]
        
        if len(data) == 0:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Rule-based detection
        data = validate_and_clean_data(data)
        rule_anomalies = detect_anomalies(data)
        rule_count = len(rule_anomalies)
        
        # ML-based detection
        wml_client = get_wml_client()
        ml_predictions = wml_client.predict_anomalies(data)
        ml_anomalies = [p for p in ml_predictions if p['is_anomaly']]
        ml_count = len(ml_anomalies)
        
        # Analysis
        total_samples = len(data)
        
        return JSONResponse(content={
            "total_samples": total_samples,
            "comparison": {
                "rule_based": {
                    "anomalies_detected": rule_count,
                    "detection_rate": round(rule_count / total_samples * 100, 2),
                    "types": list(set([a['type'] for a in rule_anomalies])),
                    "method": "Threshold-based rules"
                },
                "ml_based": {
                    "anomalies_detected": ml_count,
                    "detection_rate": round(ml_count / total_samples * 100, 2),
                    "model": "watsonx.ai Isolation Forest",
                    "method": "Statistical outlier detection"
                }
            },
            "insights": {
                "agreement": "Both methods agree on major anomalies" if abs(rule_count - ml_count) < 10 else "Methods show different sensitivities",
                "recommendation": "ML model catches subtle patterns; Rules catch known issues"
            },
            "rule_anomalies": rule_anomalies[:10],  # First 10
            "ml_anomalies": ml_anomalies[:10]  # First 10
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.get("/ml-status")
def ml_status_endpoint():
    """
    ℹ️ Check watsonx.ai integration status and model information.
    """
    if not WML_AVAILABLE:
        return JSONResponse(content={
            "status": "not_configured",
            "message": "watsonx.ai integration not available. Install dependencies and set credentials.",
            "required_env_vars": [
                "WATSONX_API_KEY",
                "WATSONX_PROJECT_ID",
                "ANOMALY_DEPLOYMENT_ID",
                "FORECAST_DEPLOYMENT_ID"
            ]
        })
    
    try:
        wml_client = get_wml_client()
        model_info = wml_client.get_model_info()
        
        return JSONResponse(content={
            "status": "configured",
            "message": "watsonx.ai integration active",
            "models": model_info
        })
        
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"watsonx.ai client error: {str(e)}"
        })


# ============================================================================
# VISUALIZER AGENT ENDPOINTS
# ============================================================================

# Import visualizer functions
from visualizer_agent import (
    generate_plotly_line_chart,
    generate_plotly_bar_chart,
    generate_plotly_pie_chart,
    generate_plotly_scatter,
    generate_anomaly_heatmap,
    generate_kpi_cards,
    generate_dashboard_config,
    TimeSeriesData,
    CategoryData,
    ScatterData
)
from chart_links import plotly_to_quickchart_url

@app.post("/visualizer/trend-chart")
def visualizer_trend_chart(data: TimeSeriesData, format: str = Query("json", description="Response format: 'json' or 'chat'")):
    """
    Generate multi-line time series chart (Plotly JSON)
    Perfect for: Energy trends, CO2 over time, production metrics
    
    Format options:
    - json: Returns Plotly config (for web apps)
    - chat: Returns text response with chart link (for watsonx Orchestrate)
    """
    try:
        chart_config = generate_plotly_line_chart(data)
        
        # For watsonx Orchestrate chat format
        if format == "chat":
            chart_url = plotly_to_quickchart_url(chart_config)
            return JSONResponse(content={
                "status": "success",
                "message": f"✅ I've created your {data.title} chart!",
                "chart_url": chart_url,
                "text_response": f"📊 **{data.title}**\n\nView your chart here: {chart_url}\n\nThis chart shows {len(data.series)} data series over {len(data.timestamps)} time points."
            })
        
        # Default: Return Plotly JSON
        return JSONResponse(content={
            "status": "success",
            "chart_type": "line",
            "config": chart_config
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.post("/visualizer/comparison-chart")
def visualizer_comparison_chart(data: CategoryData):
    """
    Generate grouped bar chart (Plotly JSON)
    Perfect for: Zone comparisons, shift analysis
    """
    try:
        chart_config = generate_plotly_bar_chart(data)
        return JSONResponse(content={
            "status": "success",
            "chart_type": "bar",
            "config": chart_config
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.post("/visualizer/pie-chart")
def visualizer_pie_chart(categories: List[str], values: List[float], title: str = "Distribution"):
    """
    Generate pie chart (Plotly JSON)
    Perfect for: Energy distribution by zone, status breakdown
    """
    try:
        chart_config = generate_plotly_pie_chart(categories, values, title)
        return JSONResponse(content={
            "status": "success",
            "chart_type": "pie",
            "config": chart_config
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.post("/visualizer/scatter-plot")
def visualizer_scatter_plot(data: ScatterData):
    """
    Generate scatter plot (Plotly JSON)
    Perfect for: Correlation analysis (energy vs production)
    """
    try:
        chart_config = generate_plotly_scatter(data)
        return JSONResponse(content={
            "status": "success",
            "chart_type": "scatter",
            "config": chart_config
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")


@app.get("/visualizer/dashboard")
def visualizer_dashboard(
    zone_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Generate complete dashboard configuration with KPI cards and multiple charts
    Perfect for: Full sustainability dashboard view
    """
    try:
        # Filter data
        data = df.copy()
        if zone_id:
            data = data[data["zone_id"] == zone_id]
        if start_date:
            data = data[data["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            data = data[data["timestamp"] <= pd.to_datetime(end_date)]
        
        # Compute KPIs
        kpis = {
            "total_energy_kwh": float(data["energy_kwh"].sum()),
            "total_co2_kg": float(data["co2_kg"].sum()),
            "total_vehicles": int(data["production_units"].sum()),
            "energy_per_vehicle_kwh": float(data["energy_kwh"].sum() / data["production_units"].sum()) if data["production_units"].sum() > 0 else 0,
            "energy_trend": 5.2,  # Mock trend %
            "co2_trend": -2.1,
            "production_trend": 3.8,
            "efficiency_trend": -1.5
        }
        
        # Prepare trend data (last 24 hours)
        recent_data = data.tail(24)
        trend_data = {
            "timestamps": recent_data["timestamp"].dt.strftime("%Y-%m-%d %H:%M").tolist(),
            "series": [
                {"name": "Energy (kWh)", "data": recent_data["energy_kwh"].tolist()},
                {"name": "CO₂ (kg)", "data": recent_data["co2_kg"].tolist()}
            ],
            "title": "Energy & CO₂ Trends (Last 24 Hours)",
            "y_axis_label": "Value"
        }
        
        # Prepare zone comparison data
        zone_energy = data.groupby("zone_id")["energy_kwh"].sum().reset_index()
        zone_data = {
            "categories": zone_energy["zone_id"].tolist(),
            "series": [
                {"name": "Energy (kWh)", "data": zone_energy["energy_kwh"].tolist()}
            ],
            "title": "Energy Consumption by Zone",
            "chart_type": "bar"
        }
        
        # Count anomalies (mock)
        anomaly_count = len(detect_anomalies(data))
        
        # Generate dashboard
        dashboard = generate_dashboard_config(kpis, trend_data, zone_data, anomaly_count)
        
        return JSONResponse(content={
            "status": "success",
            "dashboard": dashboard
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")



