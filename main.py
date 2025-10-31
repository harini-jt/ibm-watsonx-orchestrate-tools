from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
import os
import numpy as np
from datetime import datetime

app = FastAPI(
    title="Data Scout API Gateway",
    version="1.0.0",
    servers=[
        {"url": "https://data-gov-apis.vercel.app", "description": "Production Server"},
        {"url": "http://127.0.0.1:8000", "description": "Local Development Server"}
    ],
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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
    zone_id: str | None = Query(None, description="Filter by zone (e.g. ZONE-PAINT-SHOP)"),
    shift: str | None = Query(None, description="Filter by shift (e.g. SHIFT-A, SHIFT-B, SHIFT-C)"),
    start_date: str | None = Query(None, description="Start timestamp (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End timestamp (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Filter by status (OPERATIONAL/STANDBY)")
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

