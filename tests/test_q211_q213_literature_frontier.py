from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INVENTORY=ROOT/"research/frontier/q211_q213_literature_frontier_2026_10_05.json"
def test_inventory_is_preformal_and_unique():
 d=json.loads(INVENTORY.read_text(encoding="utf-8")); ids=[x["id"] for x in d["candidates"]]
 assert ids==["Q211","Q212","Q213"] and len(ids)==len(set(ids))
 for c in d["candidates"]:
  assert c["performance_authorization_allowed"] is False and c["scientific_boundary"]=="discovery_contract_only"
 assert d["safety"]=={"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False,"paid_resources_allowed":False}
def test_q213_requires_historical_intraday():
 q=next(x for x in json.loads(INVENTORY.read_text())["candidates"] if x["id"]=="Q213")
 assert "multi-year historical intraday equity bars" in q["gates"]
def test_q211_leakage_guard():
 q=next(x for x in json.loads(INVENTORY.read_text())["candidates"] if x["id"]=="Q211")
 assert "pretrained models require a training-corpus leakage audit." in q["construction_rule"]
