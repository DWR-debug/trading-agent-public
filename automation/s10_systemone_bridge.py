#!/usr/bin/env python3
"""Loopback-only SystemOne-compatible adapter for a local llama.cpp server.

This bridge is an isolated AI plumbing component. Its output is never scientific
evidence, authorization, candidate selection, promotion, or live execution.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = int(os.environ.get("S10_BRIDGE_PORT", "8765"))
LLAMA_BASE = os.environ.get("S10_LLAMA_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
MODEL = os.environ.get("S10_MODEL", "Qwen2.5-1.5B-Instruct")
TIMEOUT = max(10, min(int(os.environ.get("S10_TIMEOUT_SECONDS", "90")), 180))

SCHEMA = {
    "type": "object",
    "properties": {
        "choice": {"type": "string", "enum": ["SUPPORTED", "REFUTED", "INSUFFICIENT"]},
        "probabilities": {
            "type": "object",
            "properties": {
                "SUPPORTED": {"type": "number", "minimum": 0, "maximum": 1},
                "REFUTED": {"type": "number", "minimum": 0, "maximum": 1},
                "INSUFFICIENT": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["SUPPORTED", "REFUTED", "INSUFFICIENT"],
            "additionalProperties": False,
        },
    },
    "required": ["choice", "probabilities"],
    "additionalProperties": False,
}

def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))

def build_prompt(payload: dict) -> str:
    state = payload.get("state") or {}
    questions = payload.get("questions") or {}
    claim = str(state.get("claim", ""))
    evidence = str(state.get("evidence", ""))
    domain = str(state.get("domain", ""))
    criteria = ((questions.get("verdict") or {}).get("criteria") or {})
    return (
        "You are an evidence critic. Use ONLY the supplied evidence. Do not use outside knowledge. "
        "Return ONLY valid JSON matching the requested schema. "
        f"Domain: {domain}\nClaim: {claim}\nEvidence:\n{evidence}\n"
        f"Criteria: {json.dumps(criteria, ensure_ascii=False)}\n"
        "Choose exactly one verdict and provide probabilities that sum approximately to 1."
    )

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
                health = post_json(f"{LLAMA_BASE}/health", {})
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
            req = {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "Return only JSON. Never add commentary."},
                    {"role": "user", "content": build_prompt(payload)},
                ],
                "temperature": 0,
                "max_tokens": 160,
                "response_format": {"type": "json_schema", "schema": SCHEMA},
            }
            upstream = post_json(f"{LLAMA_BASE}/v1/chat/completions", req)
            content = ((upstream.get("choices") or [{}])[0].get("message") or {}).get("content", "")
            answer = json.loads(content)
            probs = answer.get("probabilities") or {}
            self.send_json(200, {"answers": {"verdict": {"choice": answer.get("choice"), "probabilities": probs}}})
        except Exception as exc:
            self.send_json(502, {"error": {"type": type(exc).__name__, "message": str(exc)[:500]}})

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
