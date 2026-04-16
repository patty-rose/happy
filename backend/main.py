import json
import os
import re
import subprocess
import urllib.parse
import httpx
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import asyncio
from catalog import CATALOG_TEXT, CATALOG_YEAR_FIELD, CATALOG_COUNT_CONFIG, OPENMETEO_CONFIG

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
WORLDBANK_BASE = "https://api.worldbank.org/v2/country/US/indicator"
DASHBOARD_FILE = Path(__file__).parent / "dashboard.json"

SYSTEM_PROMPT = f"""You are a civic data assistant for a Portland, Oregon policy dashboard.

Given a user question, select the most relevant datasets from the catalog and return a JSON object:

{{
  "reasoning": "2-3 sentences explaining which metrics you chose and why they're the most meaningful signal for this question. Be specific about what each metric reveals.",
  "widgets": [
    {{
      "title": "Short widget title",
      "type": "line" | "bar" | "stat",
      "source": "bls" | "worldbank" | "portland" | "portland_count",
      "series_id": "<id from catalog if source=bls or worldbank, else null>",
      "dataset_id": "<id from catalog if source=portland or portland_count, else null>",
      "description": "One sentence on what this chart reveals about the question"
    }}
  ]
}}

Return ONLY a raw JSON object, no markdown, no extra text. Choose 2-4 widgets that together tell a complete data story.
"stat" = single current value, "line" = trend over time, "bar" = discrete yearly comparison.

AVAILABLE DATA CATALOG:
{CATALOG_TEXT}
"""


class QueryRequest(BaseModel):
    prompt: str


class WidgetConfig(BaseModel):
    title: str
    type: str
    source: str
    series_id: str | None = None
    dataset_id: str | None = None
    description: str
    year_field: str | None = "YEAR_"


class QueryResponse(BaseModel):
    reasoning: str
    widgets: list[WidgetConfig]


class DashboardSave(BaseModel):
    sections: list[dict]


class HealRequest(BaseModel):
    config: dict
    error: str


def parse_claude_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser question: {req.prompt}"
    result = subprocess.run(
        ["claude", "-p", full_prompt],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"claude CLI error: {result.stderr}")
    try:
        parsed = parse_claude_json(result.stdout)
        if isinstance(parsed, list):
            parsed = {"reasoning": "", "widgets": parsed}
        # Enforce year_field from catalog for portland datasets
        for w in parsed.get("widgets", []):
            if w.get("source") == "portland" and w.get("dataset_id"):
                w["year_field"] = CATALOG_YEAR_FIELD.get(w["dataset_id"], "YEAR_")
        return parsed
    except Exception:
        raise HTTPException(status_code=500, detail=f"Could not parse claude response: {result.stdout}")


# ── Dashboard save/load ────────────────────────────────────────────────────────

@app.get("/dashboard")
def load_dashboard():
    if DASHBOARD_FILE.exists():
        return json.loads(DASHBOARD_FILE.read_text())
    return {"sections": []}


@app.post("/heal")
def heal_widget(body: HealRequest):
    """Claude diagnoses a failed widget and returns a corrected config or null."""
    prompt = f"""A data widget on a Portland policy dashboard failed to load.
Diagnose the issue using the catalog below and return a corrected widget config, or null if unfixable.

Failed config:
{json.dumps(body.config, indent=2)}

Error message:
{body.error}

AVAILABLE DATA CATALOG:
{CATALOG_TEXT}

Return ONLY raw JSON (no markdown):
{{"fixed_config": {{...corrected widget object...}}}}
OR if unfixable:
{{"fixed_config": null}}

The widget object must have: title, type, source, series_id, dataset_id, description.
Only use IDs that exist in the catalog above.
"""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return {"fixed_config": None}
    try:
        parsed = parse_claude_json(result.stdout)
        fc = parsed.get("fixed_config")
        # Enforce year_field from catalog if it's a portland dataset
        if fc and fc.get("source") == "portland" and fc.get("dataset_id"):
            fc["year_field"] = CATALOG_YEAR_FIELD.get(fc["dataset_id"], "YEAR_")
        return {"fixed_config": fc}
    except Exception:
        return {"fixed_config": None}


@app.post("/dashboard")
def save_dashboard(body: DashboardSave):
    DASHBOARD_FILE.write_text(json.dumps({"sections": body.sections}, indent=2))
    return {"ok": True}


# ── Data endpoints ─────────────────────────────────────────────────────────────

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
        period, year = obs["period"], obs["year"]
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


@app.get("/data/worldbank/{indicator}")
async def worldbank_data(indicator: str):
    url = f"{WORLDBANK_BASE}/{indicator}?format=json&mrv=25"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="World Bank API error")
    payload = resp.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise HTTPException(status_code=400, detail="Unexpected World Bank response")
    data = [
        {"date": f"{obs['date']}-01-01", "value": obs["value"]}
        for obs in reversed(payload[1])
        if obs.get("value") is not None
    ]
    return {"data": data}


TIMESTAMP_FIELDS = {"ISSUED", "CREATEDATE", "INDATE", "Est_Construction_Start_Date", "Estimated_Design_Start_Date"}


@app.get("/data/portland/{service_path:path}")
async def portland_data(service_path: str, year_field: str = "YEAR_", since_year: int = 2005):
    """Return counts aggregated by year from a Portland ArcGIS layer."""
    if year_field in TIMESTAMP_FIELDS:
        where = urllib.parse.quote(f"{year_field} >= DATE '{since_year}-01-01'")
        counts: dict[int, int] = {}
        offset = 0
        async with httpx.AsyncClient() as client:
            while True:
                url = (
                    f"{PORTLAND_BASE}/{service_path}/query"
                    f"?where={where}&outFields={year_field}"
                    f"&resultRecordCount=200&resultOffset={offset}&f=json"
                )
                resp = await client.get(url, timeout=20)
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
            f"&orderByFields={year_field}+ASC&f=json"
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


@app.get("/data/portland_count/{dataset_id:path}")
async def portland_count(dataset_id: str):
    """Return a single count stat from a Portland ArcGIS layer using catalog config."""
    config = CATALOG_COUNT_CONFIG.get(dataset_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Unknown dataset_id: {dataset_id}")
    arcgis_id = config["arcgis_id"]
    where = urllib.parse.quote(config["where"])
    url = f"{PORTLAND_BASE}/{arcgis_id}/query?where={where}&returnCountOnly=true&f=json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Portland ArcGIS error")
    payload = resp.json()
    if "error" in payload:
        raise HTTPException(status_code=400, detail=str(payload["error"]))
    count = payload.get("count", 0)
    year = datetime.now(tz=timezone.utc).year
    return {"data": [{"date": f"{year}-01-01", "value": count}], "label": config["label"]}


# ── Open-Meteo (Portland weather history, no key) ─────────────────────────────

OPENMETEO_BASE = "https://archive-api.open-meteo.com/v1/archive"
PORTLAND_LAT, PORTLAND_LON = 45.5051, -122.6750


@app.get("/data/openmeteo/{variable}")
async def openmeteo_data(variable: str):
    cfg = OPENMETEO_CONFIG.get(variable)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Unknown Open-Meteo variable: {variable}")
    api_var, agg = cfg
    url = (
        f"{OPENMETEO_BASE}?latitude={PORTLAND_LAT}&longitude={PORTLAND_LON}"
        f"&start_date=2000-01-01&end_date=2024-12-31"
        f"&daily={api_var}&timezone=America%2FLos_Angeles"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Open-Meteo API error")
    payload = resp.json()
    times = payload["daily"]["time"]
    values = payload["daily"][api_var]
    yearly: dict[str, list[float]] = {}
    for t, v in zip(times, values):
        if v is None:
            continue
        yr = t[:4]
        yearly.setdefault(yr, []).append(v)
    if agg == "mean":
        data = [{"date": f"{yr}-01-01", "value": round(sum(vs) / len(vs), 2)}
                for yr, vs in sorted(yearly.items()) if vs]
    else:
        data = [{"date": f"{yr}-01-01", "value": round(sum(vs), 1)}
                for yr, vs in sorted(yearly.items()) if vs]
    return {"data": data}


# ── USGS Water Services (streamflow, no key) ──────────────────────────────────

USGS_WATER_BASE = "https://waterservices.usgs.gov/nwis/dv/"


@app.get("/data/usgs_water/{series_id}")
async def usgs_water_data(series_id: str):
    """series_id format: {site_number}-{parameter_code}, e.g. 14211720-00060"""
    if "-" not in series_id:
        raise HTTPException(status_code=400, detail="series_id must be {site}-{param}")
    site, param = series_id.rsplit("-", 1)
    url = (
        f"{USGS_WATER_BASE}?format=json&sites={site}&parameterCd={param}"
        f"&startDT=2000-01-01&endDT=2024-12-31&statCd=00003"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="USGS Water Services error")
    payload = resp.json()
    try:
        ts = payload["value"]["timeSeries"][0]["values"][0]["value"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=400, detail="Unexpected USGS response structure")
    yearly: dict[str, list[float]] = {}
    for obs in ts:
        try:
            v = float(obs["value"])
            if v < 0:
                continue
            yr = obs["dateTime"][:4]
            yearly.setdefault(yr, []).append(v)
        except (ValueError, KeyError):
            pass
    data = [{"date": f"{yr}-01-01", "value": round(sum(vs) / len(vs), 1)}
            for yr, vs in sorted(yearly.items()) if vs]
    return {"data": data}


# ── USGS Earthquake Hazards (annual counts, no key) ───────────────────────────

USGS_QUAKE_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/count"

QUAKE_REGIONS = {
    "pnw": {"minlatitude": 44.5, "maxlatitude": 47.0, "minlongitude": -124.5, "maxlongitude": -121.0},
}


@app.get("/data/usgs_quake/{region}")
async def usgs_quake_data(region: str):
    bounds = QUAKE_REGIONS.get(region)
    if not bounds:
        raise HTTPException(status_code=404, detail=f"Unknown region: {region}")

    async def count_year(client: httpx.AsyncClient, year: int) -> tuple[int, int]:
        params = {**bounds, "minmagnitude": "2.5",
                  "starttime": f"{year}-01-01", "endtime": f"{year + 1}-01-01"}
        try:
            r = await client.get(USGS_QUAKE_BASE, params=params, timeout=15)
            return year, int(r.text.strip()) if r.status_code == 200 else 0
        except Exception:
            return year, 0

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[count_year(client, y) for y in range(2000, 2025)])

    data = [{"date": f"{yr}-01-01", "value": cnt} for yr, cnt in sorted(results)]
    return {"data": data}


# ── USAspending.gov (federal spending in Oregon, no key) ──────────────────────

USASPENDING_BASE = "https://api.usaspending.gov/api/v2/search/spending_over_time/"


@app.get("/data/usaspending/{state}")
async def usaspending_data(state: str):
    body = {
        "group": "fiscal_year",
        "filters": {
            "recipient_locations": [{"country": "USA", "state": state.upper()}],
            "time_period": [{"start_date": "2008-10-01", "end_date": "2024-09-30"}],
        },
        "subawards": False,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(USASPENDING_BASE, json=body, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="USAspending API error")
    payload = resp.json()
    data = [
        {
            "date": f"{r['time_period']['fiscal_year']}-01-01",
            "value": round(r["aggregated_amount"] / 1_000_000_000, 2),
        }
        for r in payload.get("results", [])
        if r.get("aggregated_amount") is not None
    ]
    data.sort(key=lambda d: d["date"])
    return {"data": data}
