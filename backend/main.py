import json
import os
import subprocess
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://happyy.exe.xyz",
        "https://happyy.exe.xyz:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# BLS public API v1 (no key required)
BLS_BASE = "https://api.bls.gov/publicAPI/v1/timeseries/data"

# Portland Open Data (Socrata, no key required for basic reads)
PORTLAND_BASE = "https://data.portlandoregon.gov/resource"

SYSTEM_PROMPT = """You are a civic data assistant for a Portland, Oregon policy dashboard.
Given a natural language query, respond with ONLY a JSON object (no markdown, no explanation) with this shape:
{
  "title": "Widget title",
  "type": "line" | "bar" | "stat",
  "source": "bls" | "portland",
  "series_id": "BLS series ID if source=bls, else null",
  "dataset_id": "Socrata dataset ID (e.g. i4jz-ngpf) if source=portland, else null",
  "description": "One sentence describing what this shows"
}

Available BLS series (source=bls):
- LASST410000000000003: Oregon unemployment rate (%)
- LAUMT412638000000003: Portland-Metro unemployment rate (%)
- SMS41000000000000001: Oregon total nonfarm employment (thousands)
- SMS41000000500000001: Oregon construction employment
- SMS41000000600000001: Oregon manufacturing employment
- SMU41262800000000001: Portland-Metro total employment

Available Portland Open Data datasets (source=portland):
- i4jz-ngpf: Building permits issued
- ys7h-65et: Portland parks and recreation facilities
- tmfn-bw26: Portland street paving and maintenance
- rh8a-yr3v: Police calls for service (recent)

Match the user's query to the best available series or dataset. For employment/unemployment topics use BLS. For city permits, parks, or local services use Portland Open Data.
"""


class QueryRequest(BaseModel):
    prompt: str


class WidgetConfig(BaseModel):
    title: str
    type: str
    source: str
    series_id: str | None
    dataset_id: str | None
    description: str


@app.post("/query", response_model=WidgetConfig)
def query(req: QueryRequest):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser query: {req.prompt}"
    result = subprocess.run(
        ["claude", "-p", full_prompt],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"claude CLI error: {result.stderr}")
    try:
        config = json.loads(result.stdout.strip())
        return config
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Could not parse claude response: {result.stdout}")


@app.get("/data/bls/{series_id}")
async def bls_data(series_id: str):
    url = f"{BLS_BASE}/{series_id}?latest=false"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="BLS API error")
    payload = resp.json()
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise HTTPException(status_code=400, detail=payload.get("message", ["BLS error"])[0])
    series_data = payload["Results"]["series"][0]["data"]
    # BLS returns newest first; reverse and build date strings
    data = []
    for obs in reversed(series_data):
        period = obs["period"]  # e.g. M01..M12 or Q01..Q04 or A01
        year = obs["year"]
        if period.startswith("M"):
            date = f"{year}-{period[1:]}-01"
        elif period.startswith("Q"):
            month = str((int(period[1:]) - 1) * 3 + 1).zfill(2)
            date = f"{year}-{month}-01"
        else:
            date = f"{year}-01-01"
        try:
            data.append({"date": date, "value": float(obs["value"])})
        except ValueError:
            pass
    return {"data": data}


@app.get("/data/portland/{dataset_id}")
async def portland_data(dataset_id: str, limit: int = 50):
    url = f"{PORTLAND_BASE}/{dataset_id}.json?$limit={limit}&$order=:id"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Portland Open Data error")
    return {"data": resp.json()}
