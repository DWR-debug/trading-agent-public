"""Q219 options-source breadth gate.

Discovery/PIT infrastructure only. This module does not read returns or
authorize ranking, tuning, performance, promotion or live execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

Q129_CONTRACT = "research/governance/q129_options_source_contract_2026_10_03.json"
Q129_RELEASE = "https://api.github.com/repos/lambdaclass/options_portfolio_backtester/releases/289029018"
ALT_STORE = "https://github.com/piekstra/options-data"
CBOE_ARCHIVE = "https://www.cboe.com/us/options/market_statistics/historical_data/"

def fetch(url:str)->tuple[int,str,bytes]:
    req=urllib.request.Request(url,headers={"User-Agent":"TradingAgent-Public-Q219-Breadth-Gate/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return int(getattr(r,"status",200)),r.headers.get("Content-Type",""),r.read()

def run(output:Path)->dict:
    contract=json.loads(Path(Q129_CONTRACT).read_text(encoding="utf-8"))
    status,ctype,body=fetch(Q129_RELEASE)
    release=json.loads(body.decode("utf-8"))
    option_assets=[a for a in release.get("assets",[]) if str(a.get("name","")).endswith("_options.parquet")]
    status_alt,ctype_alt,body_alt=fetch(ALT_STORE)
    alt_text=body_alt.decode("utf-8",errors="replace")
    status_cboe,ctype_cboe,body_cboe=fetch(CBOE_ARCHIVE)
    cboe_text=re.sub(r"\s+"," ",body_cboe.decode("utf-8",errors="replace")).upper()
    option_names=[str(a.get("name","")) for a in option_assets]
    underlying_symbols=sorted({x.split("_options.parquet")[0] for x in option_names})
    payload={
        "schema_version":1,
        "record_type":"q219_options_source_breadth_gate",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "candidate_id":"Q219",
        "q129_release_id":release.get("id"),
        "q129_release_tag":release.get("tag_name"),
        "q129_option_asset_count":len(option_assets),
        "q129_option_asset_names":option_names,
        "q129_option_underlyings":underlying_symbols,
        "q129_is_broad_individual_equity_option_source":bool(any(s not in {"SPY","QQQ","IWM"} for s in underlying_symbols)),
        "q129_claimed_broad_source_requires_direct_validation":contract.get("broad_source_lead",{}).get("status")=="BREADTH_LEAD_REQUIRES_DIRECT_HTTP_VALIDATION",
        "piekstra_repo_http_200":status_alt==200,
        "piekstra_data_is_gitignored": "gitignored" in alt_text.lower(),
        "piekstra_requires_alpaca_credentials": "ALPACA_API_KEY_ID" in alt_text and "ALPACA_API_SECRET_KEY" in alt_text,
        "piekstra_stated_scope_two_years": "2 YEARS" in alt_text.upper() and "OPTIONS DATA IS ~1.5 GB" in alt_text.upper(),
        "cboe_archive_http_200":status_cboe==200,
        "cboe_volume_archive_only": "EQUITY OPTION VOLUME ARCHIVE" in cboe_text and "VOLUME" in cboe_text,
        "cboe_is_quotes_iv_oi_source_proven":False,
        "free_individual_equity_option_history_proven":False,
        "scientific_evidence":False,
        "performance_authorization":False,
        "holdout_selection":False,
        "ranking":False,
        "tuning":False,
        "promotion":False,
        "live_execution":False,
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    payload["receipt_fingerprint"]=hashlib.sha256(canonical).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return payload

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); args=ap.parse_args()
    print(json.dumps(run(args.output),sort_keys=True))