from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import requests
from mangum import Mangum

class InfrastructureRecord(BaseModel):
    property_id: str
    category: str
    maintained_by: str
    ward_number: str
    address: str
    unique_id: str

app = FastAPI(title="Data Scout API Gateway")

def get_ogd_api_key(api_key: str = Query(...)):
    if not api_key:
        raise HTTPException(status_code=400, detail="OGD API key is required.")
    return api_key

@app.get("/infrastructure/coimbatore", response_model=List[InfrastructureRecord])
def fetch_infrastructure_data(limit: int = Query(10, ge=1, le=500), ogd_api_key: str = Depends(get_ogd_api_key)):
    resource_id = "c632089c-7e35-4a9a-859c-c92eee291e71"
    api_url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {"api-key": ogd_api_key, "format": "json", "limit": limit}
    response = requests.get(api_url, params=params, timeout=10)
    response.raise_for_status()
    records = response.json().get("records", [])
    return [
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

@app.get("/weather/flood_risk")
def fetch_flood_risk_data(ward_numbers: str = Query(...)):
    wards = [w.strip() for w in ward_numbers.split(",") if w.strip()]
    risk_data = []
    for ward in wards:
        risk_data.append({
            "ward_number": ward,
            "flood_probability_score": 0.85 if ward in ["45", "49"] else (0.4 if ward == "48" else 0.15),
            "last_updated": "2025-10-27T10:00:00Z",
        })
    return risk_data

# ✅ Explicit function for Vercel (fixes issubclass issue)
asgi_handler = Mangum(app)

def handler(event, context):
    """AWS Lambda compatible handler for Vercel."""
    return asgi_handler(event, context)
