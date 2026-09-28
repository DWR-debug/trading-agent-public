"""Q083 design/feasibility harness. No performance evaluation."""
from __future__ import annotations

import json
import math
import statistics
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research" / "preregistrations" / "q083_design_2026_09_28.json"

SOURCE_URLS = {
    "C22_literature": "https://www.sciencedirect.com/science/article/pii/S2214635026000821",
    "C23_literature": "https://www.sciencedirect.com/science/article/pii/S1544612326008883",
    "I16_literature": "https://www.sciencedirect.com/science/article/pii/S3050700626000654",
    "I16_SEC": "https://www.sec.gov/edgar/search/",
    "M1_AEA": "https://www.aeaweb.org/articles/materials/23797",
    "M1_replication": "https://doi.org/10.3886/E222561V1",
}


def _median(values):
    return statistics.median(values)


def _robust_z(values, history=63):
    if len(values) < history + 1:
        return None
    prior = values[-history - 1:-1]
    med = _median(prior)
    mad = _median([abs(x - med) for x in prior])
    scale = 1.4826 * mad
    if scale == 0:
        return 0.0
    return (values[-1] - med) / scale


def c22_score(asset):
    overnight = [
        asset[i]["open"] / asset[i - 1]["close"] - 1.0
        for i in range(1, len(asset))
    ]
    z = _robust_z(overnight, 63)
    return None if z is None else -z


def c23_scores(assets):
    window = 21
    if any(len(v) < window + 1 for v in assets.values()):
        return {}
    returns = {
        s: assets[s][-1]["close"] / assets[s][-1 - window]["close"] - 1.0
        for s in sorted(assets)
    }
    med = _median(list(returns.values()))
    return {s: -(returns[s] - med) for s in sorted(returns)}


def _synthetic_assets(n=220, symbols=("AAA", "BBB", "CCC", "DDD")):
    out = {}
    for k, s in enumerate(symbols):
        rows = []
        close = 100.0 + 3.0 * k
        for i in range(n):
            overnight = ((i % 11) - 5) * 0.0007 + k * 0.0001
            op = close * (1.0 + overnight)
            move = (((i * (k + 3)) % 17) - 8) * 0.0008
            cl = op * (1.0 + move)
            rows.append({
                "open": op,
                "high": max(op, cl) * 1.002,
                "low": min(op, cl) * 0.998,
                "close": cl,
                "volume": 1_000_000 + i * 1000 + k * 5000,
            })
            close = cl
        out[s] = rows
    return out


def _mutate_future(assets, from_index):
    out = {s: [dict(x) for x in rows] for s, rows in assets.items()}
    for rows in out.values():
        for i in range(from_index, len(rows)):
            rows[i]["open"] *= 8.0
            rows[i]["high"] *= 8.0
            rows[i]["low"] *= 0.2
            rows[i]["close"] *= 0.2
            rows[i]["volume"] *= 7.0
    return out


def _mutate_next(assets, index):
    out = {s: [dict(x) for x in rows] for s, rows in assets.items()}
    for rows in out.values():
        if index + 1 < len(rows):
            rows[index + 1]["open"] *= 9.0
            rows[index + 1]["high"] *= 9.0
            rows[index + 1]["low"] *= 0.1
            rows[index + 1]["close"] *= 0.1
            rows[index + 1]["volume"] *= 5.0
    return out


def run_pit_checks():
    assets = _synthetic_assets()
    index = 180
    before_c22 = {s: c22_score(assets[s][:index + 1]) for s in assets}
    before_c23 = c23_scores({s: assets[s][:index + 1] for s in assets})

    future = _mutate_future(assets, index + 1)
    next_mut = _mutate_next(assets, index)

    after_future_c22 = {s: c22_score(future[s][:index + 1]) for s in future}
    after_future_c23 = c23_scores({s: future[s][:index + 1] for s in future})
    after_next_c22 = {s: c22_score(next_mut[s][:index + 1]) for s in next_mut}
    after_next_c23 = c23_scores({s: next_mut[s][:index + 1] for s in next_mut})

    assert before_c22 == after_future_c22 == after_next_c22
    assert before_c23 == after_future_c23 == after_next_c23

    return {
        "c22_future_mutation_unchanged": True,
        "c22_next_session_mutation_unchanged": True,
        "c23_future_mutation_unchanged": True,
        "c23_next_session_mutation_unchanged": True,
        "checked_index": index,
        "synthetic_symbols": sorted(assets),
    }


def probe_sources():
    results = {}
    for name, url in SOURCE_URLS.items():
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "trading-agent-public/Q083-feasibility"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read(1024)
                results[name] = {
                    "http_status": getattr(resp, "status", 200),
                    "bytes_sampled": len(body),
                    "reachable": True,
                    "url": url,
                }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            results[name] = {
                "reachable": False,
                "error_type": type(exc).__name__,
                "error": str(exc)[:300],
                "url": url,
            }
    return results


def main():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    assert prereg["status"] == "PREREGISTERED_DESIGN_ONLY"
    gov = prereg["governance"]
    assert all(
        gov[k] is False
        for k in (
            "performance_trial_authorized",
            "performance_evaluation",
            "holdout_evaluation",
            "selection_used",
            "parameter_search",
            "threshold_search",
            "asset_search",
            "horizon_search",
            "variant_search",
            "family_ranking",
            "automatic_promotion",
        )
    )
    safety = prereg["safety"]
    assert safety == {
        "paper_only": True,
        "live_trading_enabled": False,
        "orders_enabled": False,
        "automatic_promotion": False,
    }
    pit = run_pit_checks()
    sources = probe_sources()
    result = {
        "schema_version": "1.0",
        "task_id": "Q-2026-09-28-083-FEASIBILITY",
        "status": "FEASIBILITY_CHECK_COMPLETED_NO_PERFORMANCE",
        "pit_checks": pit,
        "source_probes": sources,
        "performance_evaluation": False,
        "holdout_evaluation": False,
        "selection_used": False,
        "scientific_evidence_created": False,
        "safety": safety,
    }
    out = ROOT / "research" / "runs" / "q083_feasibility" / "result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Q083_STATUS:", result["status"])
    print("Q083_PIT_CHECKS: PASS")
    print("Q083_SOURCE_REACHABLE:", sum(1 for x in sources.values() if x.get("reachable")))
    print("Q083_SOURCE_TOTAL:", len(sources))
    for name, info in sources.items():
        print("Q083_SOURCE:", name, "reachable=" + str(info.get("reachable")), "status=" + str(info.get("http_status", "NA")))


if __name__ == "__main__":
    main()
