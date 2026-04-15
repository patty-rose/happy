import json
import subprocess
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = "annualreviews"  # public demo key

SYSTEM_PROMPT = """You are a civic data assistant for a Portland, Oregon policy dashboard.
Given a natural language query, respond with ONLY a JSON object (no markdown, no explanation) with this shape:
{
  "title": "Widget title",
  "type": "line" | "bar" | "stat",
  "source": "fred" | "portland" | "trimet",
  "series_id": "FRED series ID if source=fred, else null",
  "description": "One sentence describing what this shows"
}

Common FRED series relevant to Portland / Oregon:
- ORUR: Oregon unemployment rate
- MEHOINUSORA672N: Oregon median household income
- ATNHPIUS38900Q: Portland-area house price index
- ORCONS: Oregon construction employment
- CUURA422SAH: Portland CPI housing
- ORTRADE: Oregon retail trade employment
"""


class QueryRequest(BaseModel):
    prompt: str


class WidgetConfig(BaseModel):
    title: str
    type: str
    source: str
    series_id: str | None
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


@app.get("/data/fred/{series_id}")
async def fred_data(series_id: str, limit: int = 24):
    url = (
        f"{FRED_BASE}?series_id={series_id}"
        f"&api_key={FRED_API_KEY}&file_type=json"
        f"&sort_order=desc&limit={limit}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="FRED API error")
    obs = resp.json().get("observations", [])
    # Return chronological order, filter missing values
    data = [
        {"date": o["date"], "value": float(o["value"])}
        for o in reversed(obs)
        if o["value"] != "."
    ]
    return {"data": data}
