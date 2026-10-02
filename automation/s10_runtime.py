"""Safe local S10 runtime descriptor and endpoint resolver.

S10 is an optional, operator-configured local System-One-compatible interface.
No remote endpoints, credentials, shell commands, or live-trading hooks are accepted.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_PATH = Path.home() / ".trading-agent" / "s10_interface.json"
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
SECRET_KEYS = {"token", "api_key", "apikey", "password", "secret", "authorization", "credential", "credentials"}


class S10ConfigError(ValueError):
    pass


def descriptor_path() -> Path:
    raw = os.environ.get("S10_INTERFACE_PATH")
    return Path(raw).expanduser() if raw else DEFAULT_PATH


def _check_no_secret_keys(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().lower() in SECRET_KEYS or any(x in str(key).lower() for x in ("token", "password", "secret", "credential", "authorization")):
                raise S10ConfigError(f"secret-bearing S10 descriptor key is forbidden: {path}.{key}")
            _check_no_secret_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            _check_no_secret_keys(child, f"{path}[{i}]")


def _protocol_path(value: object) -> str:
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//") or "://" in value or any(ch in value for ch in ("?", "#")):
        raise S10ConfigError("protocol_path must be a local absolute path without query/fragment")
    return value


def _local_base_url(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise S10ConfigError("base_url is required")
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"}:
        raise S10ConfigError("S10 base_url must use http/https")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise S10ConfigError("S10 endpoint must be loopback-only")
    if parsed.username or parsed.password:
        raise S10ConfigError("S10 endpoint must not embed credentials")
    return value.strip().rstrip("/")


def load_descriptor(path: Path | None = None) -> dict[str, object]:
    path = path or descriptor_path()
    if not path.is_file():
        base = os.environ.get("S10_BASE_URL") or os.environ.get("S10_ENDPOINT")
        model = os.environ.get("S10_MODEL")
        if base or model:
            try:
                if not isinstance(model, str) or not model.strip():
                    raise S10ConfigError("S10_MODEL is required")
                return {
                    "available": True,
                    "status": "S10_CONFIGURED_ENV",
                    "path": "<environment>",
                    "mode": "systemone_http",
                    "base_url": _local_base_url(base),
                    "model": model.strip() if isinstance(model, str) and model.strip() else None,
                    "protocol_path": _protocol_path(os.environ.get("S10_PROTOCOL_PATH", "/v1/systemone")),
                    "timeout_seconds": max(5, min(int(os.environ.get("S10_TIMEOUT_SECONDS", "90")), 180)),
                }
            except (S10ConfigError, TypeError, ValueError) as exc:
                return {"available": False, "status": "S10_DESCRIPTOR_INVALID", "path": "<environment>", "error": str(exc)}
        return {"available": False, "status": "S10_UNAVAILABLE", "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "status": "S10_DESCRIPTOR_INVALID", "path": str(path), "error": type(exc).__name__}
    try:
        _check_no_secret_keys(payload)
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise S10ConfigError("unsupported S10 descriptor schema")
        if payload.get("enabled") is not True:
            return {"available": False, "status": "S10_DISABLED", "path": str(path)}
        mode = payload.get("mode", "systemone_http")
        if mode != "systemone_http":
            raise S10ConfigError("only systemone_http is supported")
        base_url = _local_base_url(payload.get("base_url"))
        model = payload.get("model")
        if not isinstance(model, str) or not model.strip():
            raise S10ConfigError("model is required")
        protocol_path = _protocol_path(payload.get("protocol_path", "/v1/systemone"))
        return {
            "available": True,
            "status": "S10_CONFIGURED",
            "path": str(path),
            "mode": mode,
            "base_url": base_url,
            "model": model.strip(),
            "protocol_path": protocol_path,
            "timeout_seconds": max(5, min(int(payload.get("timeout_seconds", 90)), 180)),
        }
    except (S10ConfigError, TypeError, ValueError) as exc:
        return {"available": False, "status": "S10_DESCRIPTOR_INVALID", "path": str(path), "error": str(exc)}


def resolve() -> dict[str, object]:
    return load_descriptor()
