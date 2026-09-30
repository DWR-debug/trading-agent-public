"""Hard-wired Free-only Mistral API adapter for bounded research support."""
from __future__ import annotations
import json,urllib.error,urllib.request
from typing import Any
ENDPOINT="https://api.mistral.ai/v1/chat/completions"
FREE_MODEL="mistral-small-latest"
MAX_TOKENS=3200
TEMPERATURE=0.2
USER_AGENT="DWR-debug/trading-agent-public-free-ai"
class MistralFreeError(ValueError):
    """Raised when the fixed free-only Mistral contract is violated."""
def call_mistral_free(prompt:str,*,api_key:str,timeout_seconds:int=60)->dict[str,Any]:
    if not api_key.strip(): raise MistralFreeError("MISTRAL_API_KEY is missing.")
    if not prompt.strip(): raise MistralFreeError("Prompt must not be empty.")
    if timeout_seconds<1: raise MistralFreeError("timeout_seconds must be positive.")
    payload={"model":FREE_MODEL,"messages":[
        {"role":"system","content":"You are a bounded research-support worker. Return final worker material only. Never claim deterministic validation, performance evidence, promotion, or live-trading authorization."},
        {"role":"user","content":prompt}],
        "temperature":TEMPERATURE,"max_tokens":MAX_TOKENS}
    req=urllib.request.Request(ENDPOINT,data=json.dumps(payload,separators=(",",":")).encode(),method="POST",
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json","User-Agent":USER_AGENT})
    try:
        with urllib.request.urlopen(req,timeout=timeout_seconds) as response:
            raw=response.read(120_000).decode("utf-8","replace"); status=int(response.status)
    except urllib.error.HTTPError as exc:
        detail=exc.read(12_000).decode("utf-8","replace")
        if exc.code in {402,429}: return {"status":"RATE_LIMITED" if exc.code==429 else "FAILED_PROVIDER","returncode":exc.code,"content":"","error":f"Mistral HTTP {exc.code}: {detail}"}
        raise MistralFreeError(f"Mistral HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MistralFreeError(f"Mistral network error: {exc.reason}") from exc
    if not 200<=status<300: raise MistralFreeError(f"Unexpected Mistral HTTP status {status}.")
    try:data=json.loads(raw)
    except json.JSONDecodeError as exc: raise MistralFreeError("Mistral returned non-JSON output.") from exc
    choices=data.get("choices")
    if not isinstance(choices,list) or not choices: raise MistralFreeError("Mistral response contains no choices.")
    msg=choices[0].get("message") if isinstance(choices[0],dict) else None
    content=msg.get("content") if isinstance(msg,dict) else None
    if isinstance(content,str) and not content.strip(): content=None
    if not isinstance(content,str): raise MistralFreeError("Mistral response contains no textual content.")
    if "<|tool_call_start|>" in content: raise MistralFreeError("Mistral returned tool-call syntax instead of final worker material.")
    return {"status":"SUCCESS","returncode":0,"content":content[-20_000:],"error":"","response_id":data.get("id"),"usage":data.get("usage") if isinstance(data.get("usage"),dict) else None}
