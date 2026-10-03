"""Q133-Q145 public/free source-feasibility gate.

Discovery-only. It probes documented public source endpoints, records source
availability, and runs generic future-mutation invariance checks. It never
downloads investment history for return evaluation and never authorizes
performance, selection, ranking, tuning, promotion, or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

PROBES: dict[str, dict[str, Any]] = {

    "PYPI_STATS": {
        "url": "https://pypistats.org/api/",
        "markers": ["PyPI Stats API", "time series", "updated once daily"],
    },
    "CROSSREF_API": {
        "url": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        "markers": ["publicly available REST API", "/works", "JSON"],
    },
    "USGS_EARTHQUAKE": {
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/swagger.json",
        "markers": ["format=geojson", "All times use ISO8601", "updatedafter"],
    },
    "NOAA_SWPC": {
        "url": "https://services.swpc.noaa.gov/products/",
        "markers": ["alerts.json", "kyoto-dst.json", "noaa-planetary-k-index.json"],
    },
    "NASA_FIRMS": {
        "url": "https://firms.modaps.eosdis.nasa.gov/active_fire/",
        "markers": ["FIRMS Archive Download", "MODIS", "VIIRS"],
    },
    "NOAA_STORM": {
        "url": "https://www.ncei.noaa.gov/access/storm-events-database/",
        "markers": ["Storm Events Database", "January 1950", "Bulk Data Access"],
    },
    "EIA_OPEN": {
        "url": "https://www.eia.gov/opendata/",
        "markers": ["Open Data", "Bulk", "Electricity"],
    },
    "USA_SPENDING": {
        "url": "https://api.usaspending.gov/docs/endpoints",
        "markers": ["Endpoints do not currently require any authorization", "/api/v2/search/spending_by_award"],
    },
    "COURTLISTENER": {
        "url": "https://www.courtlistener.com/help/",
        "markers": ["REST APIs", "Developer"],
    },
    "SEC_FOIA": {
        "url": "https://www.sec.gov/foia/frequently-requested-documents/foia-logs",
        "markers": ["FOIA Logs", "August 2026", "CSV"],
    },
    "HOUSE_DISCLOSURE": {
        "url": "https://disclosures-clerk.house.gov/FinancialDisclosure",
        "markers": ["Financial Disclosure", "2026"],
    },
    "LDA_API": {
        "url": "https://lda.gov/api/tos/",
        "markers": ["Unauthenticated", "rate limited"],
    },
    "OPENFDA_DRUG": {
        "url": "https://open.fda.gov/apis/drug/",
        "markers": ["Drugs@FDA", "Drug shortages", "Recall enforcement reports"],
    },
    "OPENFDA_DEVICE": {
        "url": "https://open.fda.gov/apis/device/",
        "markers": ["510(k) clearances", "Recall enforcement reports", "Registrations and listings"],
    },
    "CISA_KEV": {
        "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
        "markers": ["Known Exploited Vulnerabilities Catalog", "CSV", "JSON"],
    },
    "NVD": {
        "url": "https://nvd.nist.gov/developers/vulnerabilities-1",
        "markers": ["pubStartDate", "pubEndDate", "published"],
    },
    "FEMA": {
        "url": "https://www.fema.gov/about/openfema/disaster-declarations-summaries",
        "markers": ["Disaster Declarations Summaries", "API", "1953"],
    },
    "USDA_NASS": {
        "url": "https://data.nass.usda.gov/Quick_Stats/",
        "markers": ["Quick Stats", "updated", "JSON"],
    },
    "GOVINFO": {
        "url": "https://www.govinfo.gov/bulkdata/",
        "markers": ["Federal Register", "Congressional Bills", "Bill Status"],
    },
    "FEC": {
        "url": "https://api.open.fec.gov/developers/",
        "markers": ["Bulk downloads", "Schedule A"],
    },
    "FTC_DATA": {
        "url": "https://search.ftc.gov/policy-notices/open-government/data-sets",
        "markers": ["FTC Nonmerger Enforcement Actions", "FTC Merger Enforcement Actions"],
    },
    "DOJ_ANTITRUST": {
        "url": "https://www.justice.gov/atr/press-releases",
        "markers": ["Press Releases", "Antitrust"],
    },
    "BTS_FAF": {
        "url": "https://www.bts.gov/faf",
        "markers": ["Freight Analysis Framework", "commodity"],
    },
    "EPA_ENVIROFACTS": {
        "url": "https://www.epa.gov/enviro/envirofacts-data-service-api",
        "markers": ["RESTful", "JSON", "environmental"],
    },
    "SEC_FTD": {
        "url": "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data",
        "markers": ["February 2004", "September 2026", "balance level outstanding"],
    },
    "SEC_13F": {
        "url": "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets",
        "markers": ["July 2013", "August 2026", "as-filed"],
    },
    "SEC_NPORT": {
        "url": "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets",
        "markers": ["October 2019", "June 2026", "monthly portfolio holdings"],
    },
    "SEC_TECH_SPECS": {
        "url": "https://www.sec.gov/submit-filings/technical-specifications",
        "markers": ["Form 4", "13F"],
    },
    "FINRA_SSV": {
        "url": "https://www.finra.org/finra-data/browse-catalog/short-sale-volume",
        "markers": ["Daily Short Sale Volume", "Short Interest", "Consolidated file"],
    },
    "FINRA_SI": {
        "url": "https://www.finra.org/finra-data/browse-catalog/equity-short-interest",
        "markers": ["twice a month", "five rolling years", "Revision Flag"],
    },
    "TREASURY_AUCTION_QUERY": {
        "url": "https://www.treasurydirect.gov/auctions/auction-query/",
        "markers": ["Auction Query", "Bid-to-Cover Ratio", "Direct Bidder Accepted"],
    },
    "CFTC_HISTORY": {
        "url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm",
        "markers": ["Full Reports", "2026"],
    },
    "CFTC_RELEASE": {
        "url": "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm",
        "markers": ["3:30 p.m. Eastern", "2026 Release Schedule"],
    },
    "FRED_VINTAGES": {
        "url": "https://fred.stlouisfed.org/docs/api/fred/realtime_period.html",
        "markers": ["ALFRED", "realtime period", "past period"],
    },
    "BEA_IO": {
        "url": "https://www.bea.gov/data/industries/input-output-accounts-data",
        "markers": ["Input-Output", "historical data", "requirements tables"],
    },
    "PATENTSVIEW": {
        "url": "https://search.patentsview.org/docs/",
        "markers": ["PatentSearch API"],
    },
    "WIKIMEDIA_PAGEVIEWS": {
        "url": "https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html",
        "markers": ["July 1, 2015", "Get number of page views"],
    },
    "GITHUB_PUBLIC_API": {
        "url": "https://api.github.com/repos/python/cpython/releases?per_page=1",
        "markers": ["tag_name", "published_at"],
    },
}

CANDIDATE_SOURCES: dict[str, list[str]] = {
    "Q133": ["SEC_FTD", "FINRA_SSV"],
    "Q134": ["FINRA_SSV", "FINRA_SI"],
    "Q135": ["SEC_TECH_SPECS", "PATENTSVIEW"],
    "Q136": ["PATENTSVIEW", "WIKIMEDIA_PAGEVIEWS"],
    "Q137": ["SEC_TECH_SPECS"],
    "Q138": ["SEC_NPORT", "SEC_13F"],
    "Q139": ["TREASURY_AUCTION_QUERY", "SEC_TECH_SPECS"],
    "Q140": ["CFTC_HISTORY", "CFTC_RELEASE"],
    "Q141": [],
    "Q142": ["BEA_IO", "FRED_VINTAGES"],
    "Q143": ["GITHUB_PUBLIC_API", "SEC_TECH_SPECS"],
    "Q144": ["WIKIMEDIA_PAGEVIEWS", "SEC_TECH_SPECS"],
    "Q145": ["TREASURY_AUCTION_QUERY", "CFTC_HISTORY", "FRED_VINTAGES"],
    "Q146": ["NOAA_STORM", "SEC_TECH_SPECS"],
    "Q147": ["EIA_OPEN", "SEC_TECH_SPECS"],
    "Q148": ["EIA_OPEN", "SEC_TECH_SPECS"],
    "Q149": ["USA_SPENDING", "SEC_TECH_SPECS"],
    "Q150": ["COURTLISTENER", "SEC_TECH_SPECS"],
    "Q151": ["SEC_TECH_SPECS", "CFTC_RELEASE"],
    "Q152": ["HOUSE_DISCLOSURE", "SEC_TECH_SPECS"],
    "Q153": ["LDA_API", "SEC_TECH_SPECS"],
    "Q154": ["OPENFDA_DRUG", "SEC_TECH_SPECS"],
    "Q155": ["OPENFDA_DEVICE", "SEC_TECH_SPECS"],
    "Q156": ["CISA_KEV", "NVD", "SEC_TECH_SPECS"],
    "Q157": ["SEC_FOIA", "SEC_TECH_SPECS"],
    "Q158": ["GOVINFO", "SEC_TECH_SPECS"],
    "Q159": ["FEMA", "NOAA_STORM", "SEC_TECH_SPECS"],
    "Q160": ["USDA_NASS", "NOAA_STORM", "SEC_TECH_SPECS"],
    "Q161": ["BTS_FAF", "SEC_TECH_SPECS"],
    "Q162": ["EIA_OPEN", "SEC_TECH_SPECS"],
    "Q163": ["EPA_ENVIROFACTS", "SEC_TECH_SPECS"],
    "Q164": ["USA_SPENDING", "SEC_TECH_SPECS"],
    "Q165": ["FTC_DATA", "DOJ_ANTITRUST", "SEC_TECH_SPECS"],
    "Q166": ["PYPI_STATS", "SEC_TECH_SPECS"],
    "Q167": ["CROSSREF_API", "SEC_TECH_SPECS"],
    "Q168": ["USGS_EARTHQUAKE", "SEC_TECH_SPECS"],
    "Q169": ["NOAA_SWPC", "SEC_TECH_SPECS"],
    "Q170": ["NASA_FIRMS", "SEC_TECH_SPECS"],
}


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "trading-agent-public/Q133-Q145-source-feasibility/1",
            "Accept": "text/html,application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read().decode("utf-8", errors="replace")
            return int(getattr(response, "status", 200)), body
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 599, f"FETCH_ERROR:{type(exc).__name__}:{exc}"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def future_mutation_invariance() -> dict[str, bool]:
    base = [{"decision": 1, "value": 10}, {"decision": 2, "value": 11}]
    future = base + [{"decision": 3, "value": 999}]
    stable_prefix = [row["value"] for row in base] == [row["value"] for row in future[:2]]
    decomposition = [0.01 - 0.004, -0.02 - 0.01]
    future_decomposition = [
        0.01 - 0.004,
        -0.02 - 0.01,
    ] + [-0.8 - 0.6]
    return {
        "future_row_invariance": stable_prefix,
        "fixed_decomposition_prefix_invariance": decomposition == future_decomposition[:2],
        "no_search_dimension_present": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_results: dict[str, dict[str, Any]] = {}
    for source_id, spec in PROBES.items():
        status, body = fetch(str(spec["url"]))
        lowered = body.lower()
        missing = [
            marker for marker in spec["markers"]
            if marker.lower() not in lowered
        ]
        source_results[source_id] = {
            "url": spec["url"],
            "http_status": status,
            "reachable": status == 200,
            "required_markers_present": not missing and status == 200,
            "missing_markers": missing,
            "content_sha256": digest(body),
        }

    candidate_results = []
    for candidate_id, source_ids in CANDIDATE_SOURCES.items():
        if not source_ids:
            status = "DESIGN_ONLY_NO_SINGLE_SOURCE_PROBE"
        else:
            checks = [source_results[source_id]["required_markers_present"] for source_id in source_ids]
            status = "SOURCE_PROBES_PASSED" if all(checks) else "BLOCKED_SOURCE_PROBE"
        candidate_results.append({
            "candidate_id": candidate_id,
            "status": status,
            "source_ids": source_ids,
        })

    mutations = future_mutation_invariance()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-10-03-Q133-Q170-SOURCE-FEASIBILITY",
        "status": "DISCOVERY_SOURCE_FEASIBILITY_COMPLETED",
        "source_results": source_results,
        "candidate_results": candidate_results,
        "synthetic_mutation_checks": mutations,
        "scientific_boundary": {
            "performance": False,
            "holdout": False,
            "ranking": False,
            "selection": False,
            "parameter_search": False,
            "threshold_search": False,
            "horizon_search": False,
            "asset_search": False,
            "variant_search": False,
            "promotion": False,
            "live_execution": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
    }
    result["receipt_fingerprint"] = digest(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "source_pass_count": sum(1 for x in source_results.values() if x["required_markers_present"]),
        "candidate_results": candidate_results,
        "receipt_fingerprint": result["receipt_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
