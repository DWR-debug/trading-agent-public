from copy import deepcopy

import pytest

from automation.q104_i19_13f_historical_identity_census import SHARDS as CENSUS_SHARDS
from automation.q104_i19_13f_historical_identity_census_merge import (
    EXPECTED_SHARDS,
    build_receipt,
    canonical_fingerprint,
    seal,
)

SYMBOLS = ("SPGI", "NDAQ", "AMP", "RJF", "WMB", "VLO", "DVN", "EMN")
CUSIPS = {
    "SPGI": ["78409V104"],
    "NDAQ": ["631103108"],
    "AMP": ["03076C106"],
    "RJF": ["754730109"],
    "WMB": ["278865100"],
    "VLO": ["91913Y100"],
    "DVN": ["25179M103"],
    "EMN": ["03823U102"],
}
SPECS = (
    ("2013-2016", "13", "2013-07-01", "2013-08-15", "2013-06-30"),
    ("2017-2018", "17", "2017-01-01", "2017-05-15", "2017-03-31"),
    ("2019-2020", "19", "2019-01-01", "2019-05-15", "2019-03-31"),
    ("2021-2022", "21", "2021-01-01", "2021-05-15", "2021-03-31"),
    ("2023", "23", "2023-01-01", "2023-05-15", "2023-03-31"),
    ("2024-2025-09", "24", "2024-01-01", "2024-05-15", "2024-03-31"),
)


def make_shard(shard, year, period_start, filing_date, report_period):
    accession = f"0000000001-{year}-000001"
    header_url = (
        "https://www.sec.gov/Archives/edgar/data/1/"
        f"{accession.replace('-', '')}/{accession}-index-headers.html"
    )
    record = {
        "accession": accession,
        "filer_cik": "0000000001",
        "filing_date": filing_date,
        "period": report_period,
        "submission_type": "13F-HR",
        "acceptance_datetime": f"{filing_date}T16:15:42",
        "acceptance_timezone": "America/New_York",
        "acceptance_clock_basis": "SEC_EDGAR_SGML_ACCEPTANCE_DATETIME",
        "source_url": header_url,
        "header_sha256": "b" * 64,
        "header_bytes": 128,
    }
    hits = {}
    for symbol in SYMBOLS:
        selected = symbol == "SPGI"
        hits[symbol] = {
            "row_count": 1 if selected else 0,
            "cusips": CUSIPS[symbol] if selected else [],
            "issuer_names": ["Issuer SPGI"] if selected else [],
            "class_names": ["COM"] if selected else [],
            "accessions": [accession] if selected else [],
            "filing_dates": [filing_date] if selected else [],
            "periods": [report_period] if selected else [],
            "acceptance_records": {accession: record} if selected else {},
            "acceptance_complete": True,
        }
    archive = {
        "archive": {
            "url": (
                "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/"
                f"{shard}.zip"
            ),
            "label": shard,
            "period_start": period_start,
        },
        "archive_sha256": "a" * 64,
        "archive_bytes": 1024,
        "target_hits": hits,
        "security_identity_conflicts": [],
        "acceptance_failures": {},
        "acceptance_record_count": 1,
        "target_unique_accession_count": 1,
    }
    payload = {
        "schema_version": "1.0",
        "task_id": f"Q-2026-10-06-104-I19-{shard}",
        "candidate_id": "Q104:I19",
        "status": "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_SOURCE_ONLY",
        "generated_at_utc": "2026-10-09T00:00:00+00:00",
        "official_source": "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets",
        "source_page_sha256": "c" * 64,
        "data_boundary": {
            "start_inclusive": "2013-07-01",
            "end_exclusive": "2025-10-01",
            "filing_cutoff": "2025-09-24",
        },
        "shard": shard,
        "shard_boundary": {
            "start_inclusive": CENSUS_SHARDS[shard][0].isoformat(),
            "end_exclusive": CENSUS_SHARDS[shard][1].isoformat(),
        },
        "discovered_archive_count_total": 50,
        "selected_archive_count": 1,
        "frozen_cusips": CUSIPS,
        "archives": [archive],
        "synthetic": {
            "hash": True,
            "matched": True,
            "future_excluded": True,
            "no_identity_conflict": True,
        },
        "coverage_summary": {},
        "identity_conflicts": [],
        "acceptance_failures": {},
        "acceptance_time_join": {
            "records_checked": 1,
            "target_unique_accessions": 1,
            "failures": 0,
            "complete": True,
            "timezone_inference": False,
        },
        "archive_completeness_for_shard": True,
        "scientific_boundary": {
            "performance_authorized": False,
            "holdout_selection_allowed": False,
            "ranking_allowed": False,
            "parameter_search_allowed": False,
            "threshold_search_allowed": False,
            "horizon_search_allowed": False,
            "promotion_allowed": False,
            "live_execution_allowed": False,
        },
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
            "automatic_promotion": False,
        },
        "next_gate": "historical security-identity closure + SEC acceptance-time join + concept-specific PIT compiler + independent reproduction",
    }
    return seal(payload)


def sample_shards():
    return [make_shard(*spec) for spec in SPECS]


def test_complete_six_shard_census_has_verified_acceptance_join():
    receipt = build_receipt(sample_shards(), generated_at_utc="2026-10-09T00:00:00+00:00")

    assert set(receipt["completed_shards"]) == EXPECTED_SHARDS
    assert receipt["status"] == "13F_HISTORICAL_CUSIP_IDENTITY_CENSUS_COMPLETED_SOURCE_PIT_CLOCK_ONLY"
    assert receipt["archive_count"] == 6
    assert receipt["acceptance_time_join"] == {
        "target_unique_accessions": 6,
        "records_checked": 6,
        "failures": 0,
        "complete": True,
        "timezone_inference": False,
    }
    assert receipt["receipt_fingerprint"] == canonical_fingerprint(receipt)


def test_missing_shard_fails_closed():
    with pytest.raises(ValueError, match="MISSING_OR_DUPLICATE_SHARDS"):
        build_receipt(sample_shards()[:-1])


def test_shard_fingerprint_drift_fails_closed():
    payloads = sample_shards()
    payloads[0]["source_page_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="SHARD_FINGERPRINT_INVALID"):
        build_receipt(payloads)


def test_acceptance_clock_cannot_be_inferred_or_timezone_suffixed():
    payloads = sample_shards()
    payloads[0]["archives"][0]["target_hits"]["SPGI"]["acceptance_records"][
        "0000000001-13-000001"
    ]["acceptance_datetime"] += "Z"
    payloads[0] = seal(payloads[0])
    with pytest.raises(ValueError, match="ACCEPTANCE_CLOCK_INVALID"):
        build_receipt(payloads)


def test_missing_accession_acceptance_record_fails_closed():
    payloads = sample_shards()
    hit = payloads[0]["archives"][0]["target_hits"]["SPGI"]
    hit["acceptance_records"] = {}
    payloads[0] = seal(payloads[0])
    with pytest.raises(ValueError, match="ACCEPTANCE_ACCESSION_CLOSURE_FAILED"):
        build_receipt(payloads)


def test_duplicate_archive_url_fails_closed():
    payloads = sample_shards()
    payloads[1]["archives"][0]["archive"]["url"] = payloads[0]["archives"][0]["archive"]["url"]
    payloads[1] = seal(payloads[1])
    with pytest.raises(ValueError, match="DUPLICATE_OR_INVALID_ARCHIVE_URL"):
        build_receipt(payloads)


def test_compiler_accepts_only_the_clock_complete_merged_receipt():
    from automation.q104_i19_historical_pit_compiler import validate_census_receipt

    receipt = build_receipt(sample_shards(), generated_at_utc="2026-10-09T00:00:00+00:00")
    assert validate_census_receipt(receipt) == receipt

    corrupted = deepcopy(receipt)
    corrupted["acceptance_time_join"]["records_checked"] += 1
    with pytest.raises(RuntimeError, match="CENSUS_FINGERPRINT_INVALID"):
        validate_census_receipt(corrupted)
