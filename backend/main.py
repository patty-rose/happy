import json
import os
import re
import subprocess
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from catalog import CATALOG_TEXT

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLS_BASE = "https://api.bls.gov/publicAPI/v1/timeseries/data"
PORTLAND_BASE = "https://www.portlandmaps.com/od/rest/services"

SYSTEM_PROMPT = f"""You are a civic data assistant for a Portland, Oregon policy dashboard.

Given a user question, select the most relevant datasets from the catalog below and return a JSON array of widget configs — one object per dataset you want to show. Be creative and thorough: a good question deserves 2-4 widgets that together tell a complete story. Do NOT analyze or editorialize — just select and present the data.

Return ONLY a raw JSON array, no markdown, no explanation. Each element:
{{
  "title": "Short widget title",
  "type": "line" | "bar" | "stat",
  "source": "bls" | "portland",
  "series_id": "<BLS series id if source=bls, else null>",
  "dataset_id": "<ArcGIS service path if source=portland, e.g. COP_OpenData_PlanningDevelopment/MapServer/89, else null>",
  "year_field": "<year field name for portland datasets, from catalog — default YEAR_>",
  "description": "One sentence on what this data shows and why it's relevant to the question"
}}

Choose "stat" for a single current-value callout, "line" for trends over time, "bar" for comparisons.

AVAILABLE DATA CATALOG:
{CATALOG_TEXT}
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
    year_field: str | None = "YEAR_"  # ArcGIS year field; overridden per-dataset as needed


def parse_claude_json(raw: str) -> list:
    """Strip markdown fences and parse JSON from claude CLI output."""
    text = raw.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


@app.post("/query", response_model=list[WidgetConfig])
def query(req: QueryRequest):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {req.prompt}"
    result = subprocess.run(
        ["claude", "-p", full_prompt],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"claude CLI error: {result.stderr}")
    try:
        configs = parse_claude_json(result.stdout)
        if not isinstance(configs, list):
            configs = [configs]
        return configs
    except (json.JSONDecodeError, Exception) as e:
        raise HTTPException(status_code=500, detail=f"Could not parse claude response: {result.stdout}")


@app.get("/data/bls/{series_id}")
async def bls_data(series_id: str):
    url = f"{BLS_BASE}/{series_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="BLS API error")
    payload = resp.json()
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise HTTPException(status_code=400, detail=str(payload.get("message", "BLS error")))
    series_data = payload["Results"]["series"][0]["data"]
    data = []
    for obs in reversed(series_data):
        period = obs["period"]
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


@app.get("/data/portland/{service_path:path}")
async def portland_data(service_path: str, year_field: str = "YEAR_", since_year: int = 2005):
    """Query a Portland ArcGIS MapServer layer, returning counts aggregated by year.

    If year_field is a timestamp field (ISSUED), we fetch raw records and aggregate
    on the backend. Otherwise we use ArcGIS statistics groupBy.
    """
    import urllib.parse
    from datetime import datetime, timezone

    TIMESTAMP_FIELDS = {"ISSUED", "CREATEDATE", "INDATE"}

    if year_field in TIMESTAMP_FIELDS:
        # Paginate (max 200/request) and aggregate counts by year in Python
        where = urllib.parse.quote(f"{year_field} >= DATE '{since_year}-01-01'")
        counts: dict[int, int] = {}
        offset = 0
        async with httpx.AsyncClient() as client:
            while True:
                url = (
                    f"{PORTLAND_BASE}/{service_path}/query"
                    f"?where={where}"
                    f"&outFields={year_field}"
                    f"&resultRecordCount=200"
                    f"&resultOffset={offset}"
                    f"&f=json"
                )
                resp = await client.get(url, timeout=15)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail="Portland ArcGIS error")
                payload = resp.json()
                if "error" in payload:
                    raise HTTPException(status_code=400, detail=str(payload["error"]))
                features = payload.get("features", [])
                for f in features:
                    ts = f["attributes"].get(year_field)
                    if ts:
                        yr = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).year
                        counts[yr] = counts.get(yr, 0) + 1
                if len(features) < 200 or not payload.get("exceededTransferLimit"):
                    break
                offset += 200
        data = [{"date": f"{yr}-01-01", "value": cnt} for yr, cnt in sorted(counts.items())]
    else:
        stats = urllib.parse.quote('[{"statisticType":"count","onStatisticField":"OBJECTID","outStatisticFieldName":"count"}]')
        url = (
            f"{PORTLAND_BASE}/{service_path}/query"
            f"?where={urllib.parse.quote(f'{year_field}>={since_year}')}"
            f"&outStatistics={stats}"
            f"&groupByFieldsForStatistics={year_field}"
            f"&orderByFields={year_field}+ASC"
            f"&f=json"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Portland ArcGIS error")
        payload = resp.json()
        if "error" in payload:
            raise HTTPException(status_code=400, detail=str(payload["error"]))
        data = [
            {"date": f"{f['attributes'][year_field]}-01-01", "value": f["attributes"]["count"]}
            for f in payload.get("features", [])
        ]

    return {"data": data}
