"""Hard-wired Free-only Groq API adapter."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
FREE_MODEL = "openai/gpt-oss-20b"
MAX_TOKENS = 3200
TEMPERATURE = 0.2
USER_AGENT = "DWR-debug/trading-agent-public-free-ai"

class GroqFreeError(ValueError):
    """Raised when the fixed free-only Groq contract is violated."""

def call_groq_free(prompt: str, *, api_key: str, timeout_seconds: int = 60) -> dict[str, Any]:
    if not api_key.strip():
        raise GroqFreeError("GROQ_API_KEY is missing.")
    if not prompt.strip():
        raise GroqFreeError("Prompt must not be empty.")
    if timeout_seconds < 1:
        raise GroqFreeError("timeout_seconds must be positive.")
    payload = {
        'model': FREE_MODEL,
        'messages': [
            {'role':'system','content':(
                'You are a bounded research-support worker. Return final worker material only. '
                'Do not emit tool calls, hidden reasoning, or instructions to use external tools. '
                'Never claim deterministic validation, performance evidence, promotion, or live-trading authorization.'
            )},
            {'role':'user','content':prompt},
        ],
        'temperature': TEMPERATURE,
        'max_tokens': MAX_TOKENS,
    }
    body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    request=urllib.request.Request(
        ENDPOINT,data=body,method='POST',
        headers={
            'Authorization':f'Bearer {api_key}',
            'Content-Type':'application/json',
            'User-Agent':USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw=response.read(120_000).decode('utf-8',errors='replace')
            status=int(response.status)
    except urllib.error.HTTPError as exc:
        detail=exc.read(12_000).decode('utf-8',errors='replace')
        if exc.code == 429:
            return {'status':'RATE_LIMITED','returncode':429,'content':'','error':f'Groq HTTP 429: {detail}'}
        if exc.code == 402:
            return {'status':'FAILED_PROVIDER','returncode':402,'content':'','error':f'Groq HTTP 402: {detail}'}
        raise GroqFreeError(f'Groq HTTP {exc.code}: {detail}') from exc
    except urllib.error.URLError as exc:
        raise GroqFreeError(f'Groq network error: {exc.reason}') from exc
    if status < 200 or status >= 300:
        raise GroqFreeError(f'Unexpected Groq HTTP status {status}.')
    try:
        data=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GroqFreeError('Groq returned non-JSON output.') from exc
    choices=data.get('choices')
    if not isinstance(choices,list) or not choices:
        raise GroqFreeError('Groq response contains no choices.')
    message=choices[0].get('message') if isinstance(choices[0],dict) else None
    content=message.get('content') if isinstance(message,dict) else None
    if not isinstance(content,str) or not content.strip():
        raise GroqFreeError('Groq response contains no textual content.')
    if '<|tool_call_start|>' in content:
        raise GroqFreeError('Groq returned tool-call syntax instead of a final worker handoff.')
    return {
        'status':'SUCCESS','returncode':0,'content':content[-20_000:],'error':'',
        'response_id':data.get('id'),'usage':data.get('usage') if isinstance(data.get('usage'),dict) else None,
    }