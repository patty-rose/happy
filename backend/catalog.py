# Data catalog — describes every available series/dataset so Claude can reason about relevance.
# source: "bls" uses /data/bls/{series_id}
# source: "portland" uses /data/portland/{service_layer} (ArcGIS MapServer layer)

CATALOG = [
    # ── BLS Labor Data ────────────────────────────────────────────────────────
    {
        "id": "LASST410000000000003",
        "source": "bls",
        "chart_types": ["line", "stat"],
        "title": "Oregon Unemployment Rate",
        "description": "Monthly unemployment rate (%) for Oregon. Reflects share of labor force actively seeking work.",
        "topics": ["unemployment", "jobs", "labor", "economy", "workforce", "recession"],
    },
    {
        "id": "LAUMT412638000000003",
        "source": "bls",
        "chart_types": ["line", "stat"],
        "title": "Portland Metro Unemployment Rate",
        "description": "Monthly unemployment rate (%) for the Portland-Vancouver-Hillsboro metro area.",
        "topics": ["unemployment", "jobs", "portland", "metro", "labor", "workforce"],
    },
    {
        "id": "SMS41000000000000001",
        "source": "bls",
        "chart_types": ["line", "bar"],
        "title": "Oregon Total Nonfarm Employment",
        "description": "Total nonfarm payroll employment in Oregon (thousands). Broad measure of job market health.",
        "topics": ["employment", "jobs", "economy", "payroll", "workforce"],
    },
    {
        "id": "SMS41000000500000001",
        "source": "bls",
        "chart_types": ["line", "bar"],
        "title": "Oregon Construction Employment",
        "description": "Construction sector payroll employment in Oregon (thousands). Indicator of building and development activity.",
        "topics": ["construction", "building", "permits", "development", "housing", "vacancies", "jobs"],
    },
    {
        "id": "SMS41000000600000001",
        "source": "bls",
        "chart_types": ["line", "bar"],
        "title": "Oregon Manufacturing Employment",
        "description": "Manufacturing sector payroll employment in Oregon (thousands).",
        "topics": ["manufacturing", "industry", "jobs", "economy"],
    },
    {
        "id": "SMU41262800000000001",
        "source": "bls",
        "chart_types": ["line", "bar"],
        "title": "Portland Metro Total Employment",
        "description": "Total payroll employment in the Portland metro area (thousands).",
        "topics": ["employment", "jobs", "portland", "metro", "workforce", "economy"],
    },

    # ── Portland Open Data (ArcGIS / portlandmaps.com) ────────────────────────
    # These return counts aggregated by year, suitable for bar/line charts.
    {
        "id": "COP_OpenData_PlanningDevelopment/MapServer/89",
        "source": "portland",
        "chart_types": ["bar", "line"],
        "title": "Portland Residential Building Permits (by Year)",
        "description": "Count of residential building permits issued per year in Portland. Proxy for housing construction activity and development interest.",
        "topics": ["building", "permits", "construction", "development", "housing", "vacancies", "downtown", "zoning", "residential"],
    },
    {
        "id": "COP_OpenData_PlanningDevelopment/MapServer/126",
        "source": "portland",
        "chart_types": ["bar", "line"],
        "title": "Portland Residential Demolitions (by Year)",
        "description": "Count of residential demolition permits issued per year. Indicates teardown/redevelopment activity and potential vacancy creation.",
        "topics": ["demolition", "teardown", "redevelopment", "vacancies", "housing", "construction", "permits"],
        "year_field": "ISSUED",  # epoch ms timestamp — backend converts to year
        "since_year": 2005,
    },
]

CATALOG_TEXT = "\n".join(
    f'- [{e["source"].upper()} | {e["id"]}] {e["title"]}: {e["description"]} '
    f'(topics: {", ".join(e["topics"])}; chart types: {", ".join(e["chart_types"])})'
    for e in CATALOG
)

# Authoritative year_field lookup — never rely on Claude for this
CATALOG_YEAR_FIELD: dict[str, str] = {
    e["id"]: e.get("year_field", "YEAR_")
    for e in CATALOG
    if e["source"] == "portland"
}
