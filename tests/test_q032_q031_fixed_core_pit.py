from __future__ import annotations

from pathlib import Path

from automation.strategy_pit_preflight import _load_assets


def test_pit_loader_accepts_registered_small_universe_size(tmp_path: Path) -> None:
    import csv
    for symbol in ("AA1","BB2"):
        path=tmp_path/symbol
        path.mkdir(parents=True)
        with (path/"1d.csv").open("w",newline="",encoding="utf-8") as handle:
            writer=csv.writer(handle)
            writer.writerow(["timestamp","open","high","low","close","volume"])
            for i in range(3500):
                value=100.0+i
                writer.writerow([f"2010-01-{(i%28)+1:02d}T00:00:00+00:00",value,value+1,value-1,value+0.5,1000])
    assets=_load_assets(tmp_path, expected_assets=2)
    assert set(assets)=={"AA1","BB2"}
    assert all(len(rows)==3500 for rows in assets.values())
