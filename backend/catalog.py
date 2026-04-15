# Data catalog — describes every available series/dataset.
# source: "bls"       → /data/bls/{id}
# source: "worldbank" → /data/worldbank/{id}
# source: "portland"  → /data/portland/{id}  (year-aggregated ArcGIS)
# source: "portland_count" → /data/portland_count/{id}  (static count stat)

CATALOG = [
    # ── BLS Labor Data (Oregon / Portland-Metro) ──────────────────────────────
    # Note: BLS v1 API (no key) rate-limits at ~10 req/day per IP.
    {
        "id": "LASST410000000000003",
        "source": "bls",
        "chart_types": ["line", "stat"],
        "title": "Oregon Unemployment Rate",
        "description": "Monthly unemployment rate (%) for Oregon.",
        "topics": ["unemployment", "jobs", "labor", "economy", "workforce"],
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
        "description": "Total nonfarm payroll employment in Oregon (thousands).",
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

    # ── World Bank (US national context, no API key required) ─────────────────
    {
        "id": "FP.CPI.TOTL.ZG",
        "source": "worldbank",
        "chart_types": ["line"],
        "title": "US Inflation Rate (CPI, Annual %)",
        "description": "Annual US consumer price inflation. Context for Portland cost-of-living, rent pressures, and real estate investment appetite.",
        "topics": ["inflation", "cost of living", "housing", "affordability", "economy", "rent"],
    },
    {
        "id": "NY.GDP.PCAP.KD.ZG",
        "source": "worldbank",
        "chart_types": ["line"],
        "title": "US GDP Per Capita Growth (Annual %)",
        "description": "Annual real GDP per capita growth for the US. Macro-economic context for investment and development cycles.",
        "topics": ["gdp", "economy", "growth", "recession", "investment", "development"],
    },
    {
        "id": "SL.UEM.TOTL.ZS",
        "source": "worldbank",
        "chart_types": ["line", "stat"],
        "title": "US Unemployment Rate (National)",
        "description": "National unemployment rate (% of labor force, ILO estimate). Compare against Portland-Metro for local context.",
        "topics": ["unemployment", "jobs", "labor", "national", "economy", "workforce"],
    },
    {
        "id": "SP.URB.TOTL.IN.ZS",
        "source": "worldbank",
        "chart_types": ["line"],
        "title": "US Urban Population (%)",
        "description": "Share of US population living in urban areas. Context for urbanization trends driving Portland's density and housing demand.",
        "topics": ["urbanization", "population", "density", "housing", "growth"],
    },
    {
        "id": "EN.URB.LCTY.UR.ZS",
        "source": "worldbank",
        "chart_types": ["line"],
        "title": "US Population in Largest City (%)",
        "description": "Share of urban population in the country's largest city. Indicator of urban concentration trends.",
        "topics": ["urbanization", "population", "city", "concentration"],
    },

    # ── Portland Open Data — year-aggregated ArcGIS layers ────────────────────
    {
        "id": "COP_OpenData_PlanningDevelopment/MapServer/89",
        "source": "portland",
        "chart_types": ["bar", "line"],
        "title": "Portland Residential Building Permits (by Year)",
        "description": "Count of residential building permits issued per year. Proxy for housing construction and development interest.",
        "topics": ["building", "permits", "construction", "development", "housing", "vacancies", "zoning", "residential"],
        "year_field": "YEAR_",
    },
    {
        "id": "COP_OpenData_PlanningDevelopment/MapServer/126",
        "source": "portland",
        "chart_types": ["bar", "line"],
        "title": "Portland Residential Demolitions (by Year)",
        "description": "Count of residential demolition permits per year. Indicates teardown/redevelopment churn and potential vacancy creation.",
        "topics": ["demolition", "teardown", "redevelopment", "vacancies", "housing", "construction"],
        "year_field": "ISSUED",
    },
    {
        "id": "COP_OpenData_CityProjects/MapServer/43",
        "source": "portland",
        "chart_types": ["bar"],
        "title": "Portland Capital Improvement Projects (by Start Year)",
        "description": "Count of city capital improvement projects by construction start year. Tracks public investment in Portland infrastructure.",
        "topics": ["capital", "investment", "infrastructure", "city projects", "construction", "public spending", "development"],
        "year_field": "Est_Construction_Start_Date",
    },

    # ── Portland Open Data — static count stats ────────────────────────────────
    {
        "id": "COP_OpenData_Property/MapServer/91",
        "source": "portland_count",
        "chart_types": ["stat"],
        "title": "Publicly Owned Vacant Parcels",
        "description": "Count of Portland parcels owned by public entities classified as vacant land. Direct measure of publicly held vacant property.",
        "topics": ["vacant", "land", "parcels", "downtown", "public", "property", "development", "vacancy", "empty"],
        "where": "PRPCD_DESC='VACANT LAND'",
        "label": "vacant parcels",
    },
    {
        "id": "COP_OpenData_Property/MapServer/91:all",
        "source": "portland_count",
        "chart_types": ["stat"],
        "title": "Total Publicly Owned Parcels",
        "description": "Total count of all parcels owned by public entities in Portland (city, county, state, federal).",
        "topics": ["public", "property", "land", "parcels", "government"],
        "where": "1=1",
        "arcgis_id": "COP_OpenData_Property/MapServer/91",
        "label": "public parcels",
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

# Extra params for portland_count queries
CATALOG_COUNT_CONFIG: dict[str, dict] = {
    e["id"]: {
        "where": e.get("where", "1=1"),
        "arcgis_id": e.get("arcgis_id", e["id"]),
        "label": e.get("label", "records"),
    }
    for e in CATALOG
    if e["source"] == "portland_count"
}
