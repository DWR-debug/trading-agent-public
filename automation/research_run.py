"""Immutable identity for reproducible Research runs."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from config import settings
from config.parameter_space import ParameterSpace
from research.protocol import ResearchProtocol, dataset_fingerprint


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def code_version() -> str:
    """Return the immutable CI/local code identifier when available."""
    env_sha = os.getenv("GITHUB_SHA") or os.getenv("GIT_COMMIT_SHA")
    if env_sha:
        return env_sha

    repo_root = Path(__file__).resolve().parents[1]
    try:
        local_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNVERIFIED_LOCAL_CODE"

    return local_sha or "UNVERIFIED_LOCAL_CODE"


def manifest_fingerprint(manifest: dict[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_fingerprint", None)
    return _hash(payload)


def parameter_space_identity(parameter_space: ParameterSpace) -> dict[str, Any]:
    return {
        "momentum_lookbacks": list(parameter_space.momentum_lookbacks),
        "mean_reversion_windows": list(
            parameter_space.mean_reversion_windows
        ),
        "mean_reversion_thresholds": list(
            parameter_space.mean_reversion_thresholds
        ),
        "risk_per_trade_values": list(
            parameter_space.risk_per_trade_values
        ),
        "leverage_values": list(parameter_space.leverage_values),
    }


def settings_identity() -> dict[str, Any]:
    return {
        "initial_capital_eur": settings.INITIAL_CAPITAL_EUR,
        "risk_per_trade": settings.RISK_PER_TRADE,
        "max_leverage": settings.MAX_LEVERAGE,
        "max_daily_loss_eur": settings.MAX_DAILY_LOSS_EUR,
        "max_drawdown_percent": settings.MAX_DRAWDOWN_PERCENT,
        "max_open_positions": settings.MAX_OPEN_POSITIONS,
        "paper_only": settings.PAPER_ONLY,
        "live_trading_enabled": settings.LIVE_TRADING_ENABLED,
    }


def build_run_identity(
    datasets: list[tuple[str, str]],
    store,
    protocol: ResearchProtocol,
    parameter_space: ParameterSpace,
    *,
    data_manifest_path: str | Path | None = None,
    execution_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset_entries = []

    for symbol, interval in datasets:
        candles = tuple(store.load(symbol, interval))
        if not candles:
            raise ValueError(
                f"Keine Marktdaten vorhanden: {symbol} {interval}"
            )

        dataset_entries.append(
            {
                "symbol": symbol,
                "interval": interval,
                "candle_count": len(candles),
                "data_start": candles[0].timestamp.isoformat(),
                "data_end": candles[-1].timestamp.isoformat(),
                "fingerprint": dataset_fingerprint(candles),
            }
        )

    data_manifest = None
    if data_manifest_path is not None:
        manifest_path = Path(data_manifest_path)
        if manifest_path.exists():
            data_manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            stored_manifest_fingerprint = data_manifest.get("manifest_fingerprint")
            if stored_manifest_fingerprint != manifest_fingerprint(data_manifest):
                raise ValueError(
                    "Research-Datenmanifest besitzt keinen gültigen Fingerprint."
                )

            manifest_by_key = {
                (item["symbol"], item["interval"]): item
                for item in data_manifest.get("datasets", [])
            }

            for item in dataset_entries:
                manifest_item = manifest_by_key.get(
                    (item["symbol"], item["interval"])
                )
                if manifest_item is None:
                    raise ValueError(
                        "Dataset fehlt im Research-Datenmanifest: "
                        f"{item['symbol']} {item['interval']}"
                    )
                if (
                    manifest_item.get("fingerprint")
                    != item["fingerprint"]
                    or manifest_item.get("candle_count")
                    != item["candle_count"]
                ):
                    raise ValueError(
                        "Research-Datenmanifest stimmt nicht mit "
                        f"den lokalen Daten überein: "
                        f"{item['symbol']} {item['interval']}"
                    )

    identity = {
        "identity_version": 3,
        "data_manifest": data_manifest,
        "code_version": code_version(),
        "datasets": dataset_entries,
        "protocol": asdict(protocol),
        "parameter_space": parameter_space_identity(parameter_space),
        "execution_config": dict(execution_config or {}),
        "settings": settings_identity(),
        "safety": {
            "paper_only": True,
            "live_trading_enabled": False,
            "orders_enabled": False,
        },
    }

    identity["run_fingerprint"] = _hash(identity)
    return identity


def same_run_identity(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> bool:
    expected_copy = dict(expected)
    actual_copy = dict(actual)
    expected_copy.pop("run_fingerprint", None)
    actual_copy.pop("run_fingerprint", None)
    expected_copy.pop("created_at", None)
    actual_copy.pop("created_at", None)
    return (
        expected_copy == actual_copy
        and expected.get("run_fingerprint") == _hash(actual_copy)
    )
