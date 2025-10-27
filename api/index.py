from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import requests
from mangum import Mangum  # For serverless adaptation

# --- 1. Define Schemas ---
class InfrastructureRecord(BaseModel):
    property_id: str
    category: str
    maintained_by: str
    ward_number: str
    address: str
    unique_id: str

# --- 2. App Setup ---
app = FastAPI(
    title="Data Scout API Gateway",
    description="Microservice for National Infrastructure Resilience Copilot.",
    version="1.0.0"
)

# --- 3. Dependencies ---
def get_ogd_api_key(api_key: str = Query(...)):
    if not api_key:
        raise HTTPException(status_code=400, detail="OGD API key is required.")
    return api_key

# --- 4. Routes ---
@app.get("/infrastructure/coimbatore", response_model=List[InfrastructureRecord])
def fetch_infrastructure_data(
    limit: int = Query(10, ge=1, le=500),
    ogd_api_key: str = Depends(get_ogd_api_key)
):
    resource_id = "c632089c-7e35-4a9a-859c-c92eee291e71"
    api_url = f"https://api.data.gov.in/resource/{resource_id}"

    params = {"api-key": ogd_api_key, "format": "json", "limit": limit}

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        full_data = response.json()
        records = full_data.get("records", [])
        cleaned_records = [
            {
                "property_id": str(r.get("property_id", "")),
                "category": r.get("category", ""),
                "maintained_by": r.get("maintained_by", ""),
                "ward_number": str(r.get("ward_number", "")),
                "address": r.get("address", ""),
                "unique_id": str(r.get("unique_id", "")),
            }
            for r in records
        ]
        return cleaned_records
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Data.gov.in API call failed: {e}")

@app.get("/weather/flood_risk", response_model=List[Dict[str, Any]])
def fetch_flood_risk_data(ward_numbers: str = Query(...)):
    wards = [w.strip() for w in ward_numbers.split(",") if w.strip()]
    risk_data = []
    for ward in wards:
        if ward in ["45", "49"]:
            risk_score = 0.85
        elif ward == "48":
            risk_score = 0.40
        else:
            risk_score = 0.15
        risk_data.append({
            "ward_number": ward,
            "flood_probability_score": risk_score,
            "last_updated": "2025-10-27T10:00:00Z",
        })
    return risk_data

# --- 5. Add handler for Vercel ---
handler = Mangum(app)
