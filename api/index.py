from fastapi import FastAPI, HTTPException, Depends, Query # <-- Added 'Query' here
from pydantic import BaseModel, Field
import requests
from typing import List, Dict, Any
from mangum import Mangum  # For Vercel deployment
# --- 1. Pydantic Schemas for Data Structure ---

# Schema for a single infrastructure record (the item inside the 'records' array)
class InfrastructureRecord(BaseModel):
    """Schema for a single infrastructure asset record."""
    property_id: str = Field(..., description="Unique primary identifier for the physical property.")
    category: str = Field(..., description="Type of infrastructure asset (e.g., HOSPITAL, ROAD).")
    maintained_by: str = Field(..., description="Entity responsible for maintenance (e.g., CORPORATION, PRIVATE).")
    ward_number: str = Field(..., description="The administrative ward number, used as the spatial key.")
    address: str = Field(..., description="Physical location detail.")
    unique_id: str = Field(..., description="A secondary unique identifier.")

# --- 2. Configuration and Setup ---

app = FastAPI(
    title="Data Scout API Gateway",
    description="Microservice for the National Infrastructure Resilience Copilot to fetch and fuse raw data.",
    version="1.0.0"
)

handler = Mangum(app)  # For vercel deployment

# --- 3. Custom Dependency for API Key (FIXED to use Query) ---
def get_ogd_api_key(
    # By using Query, we explicitly tell FastAPI this parameter comes from the URL query string
    api_key: str = Query(..., description="The India OGD API key.") 
):
    """Dependency that ensures the OGD API key is provided."""
    if not api_key:
        # Note: Query(..., required=True) handles this, but the explicit check is safer
        raise HTTPException(status_code=400, detail="OGD API key is required.")
    return api_key

# --- 4. Endpoints (FIXED to use Query for 'limit') ---

@app.get(
    "/infrastructure/coimbatore",
    response_model=List[InfrastructureRecord],
    summary="Fetches and parses filtered infrastructure records for Coimbatore."
)
def fetch_infrastructure_data(
    # FIX: Use Query() instead of Field() alone to define it as a query parameter
    limit: int = Query(10, ge=1, le=500, description="Max number of records to retrieve."),
    ogd_api_key: str = Depends(get_ogd_api_key) # Dependency is now correctly defined as a Query param
) -> List[Dict[str, Any]]:
    """
    Fetches raw infrastructure data from data.gov.in, extracts the 'records' array, 
    and returns a clean list of infrastructure assets.
    """
    # Replace with your actual resource ID
    resource_id = "c632089c-7e35-4a9a-859c-c92eee291e71"
    api_url = f"https://api.data.gov.in/resource/{resource_id}"

    params = {
        "api-key": ogd_api_key, # ogd_api_key is provided by the dependency
        "format": "json",
        "limit": limit
    }

    try:
        # Use a timeout for resilience
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad status codes (4xx or 5xx)
        full_data = response.json()

        # CRUCIAL STEP: EXTRACT ONLY THE RECORDS LIST
        records = full_data.get('records', [])

        # Clean the records to match the Pydantic schema (ensuring types are strings)
        cleaned_records = []
        for record in records:
            cleaned_record = {
                "property_id": str(record.get("property_id", "")),
                "category": record.get("category", ""),
                "maintained_by": record.get("maintained_by", ""),
                "ward_number": str(record.get("ward_number", "")),
                "address": record.get("address", ""),
                "unique_id": str(record.get("unique_id", ""))
            }
            cleaned_records.append(cleaned_record)
            
        return cleaned_records

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data.gov.in API call failed: {e}"
        )

@app.get(
    "/weather/flood_risk",
    response_model=List[Dict[str, Any]],
    summary="Mocks fetching flood risk data per ward number."
)
def fetch_flood_risk_data(
    ward_numbers: str = Query(..., description="Comma-separated list of ward numbers to check (e.g., '45,49,50').")
):
    """
    Mocks a call to an IMD/NDMA API to get a flood probability score for given wards.
    This is a placeholder that returns a static mock response.
    """
    risk_data = []
    
    # Process the comma-separated input string
    wards = [w.strip() for w in ward_numbers.split(',') if w.strip()]

    # Simple mock logic based on ward number
    for ward in wards:
        if ward in ['45', '49']:
            risk_score = 0.85  # High risk
        elif ward == '48':
            risk_score = 0.40  # Medium risk
        else:
            risk_score = 0.15  # Low risk

        risk_data.append({
            "ward_number": ward,
            "flood_probability_score": risk_score,
            "last_updated": "2025-10-27T10:00:00Z"
        })

    return risk_data


# # Example invocation for local testing (run with: uvicorn main:app --reload)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
