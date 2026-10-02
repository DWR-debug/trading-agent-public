#!/usr/bin/env python3
"""Loopback-only SystemOne-compatible adapter for a local llama.cpp server.

This bridge is an isolated AI plumbing component. Its output is never scientific
evidence, authorization, candidate selection, promotion, or live execution.
"""
from __future__ import annotations

import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = int(os.environ.get("S10_BRIDGE_PORT", "8765"))
LLAMA_BASE = os.environ.get("S10_LLAMA_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
MODEL = os.environ.get("S10_MODEL", "S10-Qwen2.5-1.5B")
TIMEOUT = max(10, min(int(os.environ.get("S10_TIMEOUT_SECONDS", "90")), 180))

def get_json(url: str) -> dict:
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))

def resolve_upstream_model() -> str:
    try:
        models = get_json(f"{LLAMA_BASE}/v1/models").get("data")
        ids = [
            str(row.get("id"))
            for row in (models if isinstance(models, list) else [])
            if isinstance(row, dict) and row.get("id")
        ]
        if MODEL in ids:
            return MODEL
        if ids:
            return ids[0]
    except Exception:
        pass
    return MODEL

def build_prompt(payload: dict) -> str:
    state = payload.get("state") or {}
    questions = payload.get("questions") or {}
    claim = str(state.get("claim", ""))
    evidence = str(state.get("evidence", ""))
    domain = str(state.get("domain", ""))
    criteria = ((questions.get("verdict") or {}).get("criteria") or {})
    return (
        "You are an evidence critic. Use ONLY the supplied evidence. Do not use outside knowledge. "
        "Return ONLY one valid JSON object, with no markdown and no commentary. "
        'The JSON must have exactly: {"choice":"SUPPORTED|REFUTED|INSUFFICIENT","probabilities":{"SUPPORTED":number,"REFUTED":number,"INSUFFICIENT":number}}. '
        "Probabilities must be between 0 and 1 and sum to 1. "
        f"Domain: {domain}\nClaim: {claim}\nEvidence:\n{evidence}\n"
        f"Criteria: {json.dumps(criteria, ensure_ascii=False)}"
    )

def extract_json_object(content: str) -> dict:
    text = content.strip()
    if not text:
        raise ValueError("empty_model_content")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model_did_not_return_json_object") from None
        value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("model_json_is_not_object")
    choice = value.get("choice")
    probs = value.get("probabilities")
    allowed = {"SUPPORTED", "REFUTED", "INSUFFICIENT"}
    if choice not in allowed or not isinstance(probs, dict) or set(probs) != allowed:
        raise ValueError("model_json_contract_invalid")
    values = [probs[key] for key in ("SUPPORTED", "REFUTED", "INSUFFICIENT")]
    if not all(isinstance(v, (int, float)) and math.isfinite(float(v)) and 0 <= float(v) <= 1 for v in values):
        raise ValueError("model_probabilities_invalid")
    if abs(sum(float(v) for v in values) - 1.0) > 0.05:
        raise ValueError("model_probabilities_do_not_sum_to_one")
    return {"choice": choice, "probabilities": probs}

class Handler(BaseHTTPRequestHandler):
    server_version = "S10-llama-bridge/1"

    def log_message(self, *_args) -> None:
        return

    def send_json(self, code: int, value: dict) -> None:
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            try:
                health = get_json(f"{LLAMA_BASE}/health")
            except Exception as exc:
                self.send_json(503, {"status": "unavailable", "error": type(exc).__name__})
                return
            self.send_json(200, {"status": "ok", "upstream": health.get("status"), "model": MODEL})
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/v1/systemone":
            self.send_json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            smoke_mode = payload.get("mode") == "smoke"
            req = {
                "model": resolve_upstream_model(),
                "messages": [
                    {"role": "system", "content": "Return only one JSON object. Never add commentary."},
                    {"role": "user", "content": build_prompt(payload)},
                ],
                "temperature": 0,
                "max_tokens": 48 if smoke_mode else 160,
            }
            upstream = post_json(f"{LLAMA_BASE}/v1/chat/completions", req)
            content = ((upstream.get("choices") or [{}])[0].get("message") or {}).get("content", "")
            answer = extract_json_object(content)
            self.send_json(200, {"answers": {"verdict": answer}})
        except Exception as exc:
            detail = str(exc)[:500]
            if hasattr(exc, "read"):
                try:
                    detail = exc.read().decode("utf-8")[:500]
                except Exception:
                    pass
            self.send_json(502, {"error": {"type": type(exc).__name__, "message": detail}})

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
