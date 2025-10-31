from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import pandas as pd
import requests
import os

app = FastAPI(
    title="Data Scout API Gateway",
    version="1.0.0",
    servers=[
        {"url": "https://data-gov-apis.vercel.app", "description": "Production Server"},
        {"url": "http://127.0.0.1:8000", "description": "Local Development Server"}
    ],
)
# # --- 3. Load Environment Variable ---
# API_KEY = os.getenv("API_KEY") 
# if not API_KEY:
#     raise RuntimeError("Environment variable 'API_KEY' not set.")
# Load CSV once at startup
DATA_PATH = "data/automotive_energy_data.csv"
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

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