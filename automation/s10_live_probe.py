"""Local-only, fail-closed S10 interface verification for the self-hosted runner."""
from __future__ import annotations

import json, os, re, shutil, subprocess, time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CLI_NAMES = ("s10", "s10.exe", "s10-cli", "s10-cli.exe", "s10-agent", "s10-agent.exe")
SECRET = re.compile(r"(?:TOKEN|KEY|SECRET|PASSWORD|PASS|CREDENTIAL|AUTH)", re.I)
LOCAL = {"127.0.0.1", "localhost", "::1"}

def run(cmd, timeout=5):
    try:
        return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None

def ps(script, timeout=5):
    exe = shutil.which("powershell.exe") or shutil.which("powershell")
    if not exe: return None
    return run([exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], timeout)

def parse_json(raw):
    try: return json.loads((raw or "").strip())
    except json.JSONDecodeError: return None

def local_url(raw):
    if not raw or len(raw) > 500: return None
    v = raw.strip(); v = v if re.match(r"^https?://", v, re.I) else "http://" + v
    p = urlparse(v)
    if p.hostname not in LOCAL: return None
    host = p.hostname
    if ":" in host and not host.startswith("["): host = f"[{host}]"
    return f"{p.scheme.lower()}://{host}:{p.port}{p.path or '/'}" if p.port else f"{p.scheme.lower()}://{host}{p.path or '/'}"

def http_get(url, timeout=5):
    started=time.monotonic()
    try:
        with urlopen(Request(url, headers={"User-Agent":"trading-agent-s10-probe/1"}), timeout=timeout) as r:
            raw=r.read(20000).decode("utf-8", "replace")
            try: body=json.loads(raw)
            except json.JSONDecodeError: body=None
            return {"status":r.status,"json_keys":sorted(body) if isinstance(body,dict) else None,"duration_seconds":round(time.monotonic()-started,3)}
    except HTTPError as e: return {"status":e.code,"error":f"HTTP_{e.code}","duration_seconds":round(time.monotonic()-started,3)}
    except (URLError,OSError,TimeoutError) as e: return {"status":None,"error":type(e).__name__,"duration_seconds":round(time.monotonic()-started,3)}

def http_post(url, payload, timeout=25):
    started=time.monotonic(); data=json.dumps(payload,separators=(",",":")).encode()
    try:
        req=Request(url,data=data,headers={"Content-Type":"application/json","User-Agent":"trading-agent-s10-probe/1"},method="POST")
        with urlopen(req,timeout=timeout) as r:
            raw=r.read(20000).decode("utf-8","replace")
            return {"status":r.status,"marker_present":"S10_LIVE_READY" in raw,"duration_seconds":round(time.monotonic()-started,3)}
    except HTTPError as e: return {"status":e.code,"error":f"HTTP_{e.code}","duration_seconds":round(time.monotonic()-started,3)}
    except (URLError,OSError,TimeoutError) as e: return {"status":None,"error":type(e).__name__,"duration_seconds":round(time.monotonic()-started,3)}

def main():
    result={"schema_version":1,"identity":"S10","runner_name":os.getenv("RUNNER_NAME"),"paper_only":True,"live_trading_enabled":False,"orders_enabled":False,"automatic_promotion":False,"formal_evidence_allowed":False,"secrets_collected":False}
    result["environment_keys"]=sorted(k for k in os.environ if k.upper().startswith("S10_") and not SECRET.search(k.upper()))
    result["secret_key_names_detected"]=sorted(k for k in os.environ if k.upper().startswith("S10_") and SECRET.search(k.upper()))
    result["cli"]=[]
    for n in CLI_NAMES:
        p=shutil.which(n)
        if p and not any(x["path"]==p for x in result["cli"]):
            v=run([p,"--version"])
            result["cli"].append({"name":n,"path":p,"version_returncode":None if v is None else v.returncode,"version":((v.stdout or v.stderr).strip().splitlines()[-1][:400] if v else None)})
    processes=[]
    if os.name=="nt":
        r=ps(r'''Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | ? { $_.Name -match '(?i)s10' } | select Name,ProcessId | ConvertTo-Json -Compress''')
        data=parse_json(r.stdout if r else ""); rows=data if isinstance(data,list) else ([data] if isinstance(data,dict) else [])
        processes=[{"name":str(x.get("Name","")),"pid":int(x.get("ProcessId"))} for x in rows if str(x.get("ProcessId"," ")).isdigit()]
    result["processes"]=processes
    pids=",".join(str(x["pid"]) for x in processes)
    listeners=[]
    if pids:
        r=ps(f'''$ids=@({pids}); Get-NetTCPConnection -State Listen -EA SilentlyContinue | ? {{ $ids -contains $_.OwningProcess }} | select LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress''')
        data=parse_json(r.stdout if r else ""); rows=data if isinstance(data,list) else ([data] if isinstance(data,dict) else [])
        listeners=[{"address":str(x.get("LocalAddress","")),"port":int(x.get("LocalPort")),"pid":int(x.get("OwningProcess"))} for x in rows if str(x.get("LocalPort"," ")).isdigit() and str(x.get("OwningProcess"," ")).isdigit()]
    result["listeners"]=listeners
    urls=[]
    for k,v in os.environ.items():
        if k.upper().startswith("S10_") and not SECRET.search(k.upper()) and any(t in k.upper() for t in ("_URL","_ENDPOINT","_HOST")):
            u=local_url(v); urls += [u] if u else []
    for x in listeners: urls.append(f"http://127.0.0.1:{x['port']}/")
    result["local_interfaces"]=[]
    for base in sorted(set(urls)):
        p=urlparse(base); root=f"{p.scheme}://{p.netloc}"
        checks=[]
        for path in ("/health","/v1/models","/api/tags","/"):
            u=root+path; c=http_get(u); checks.append({"url":u,**c})
            if c.get("status") and c["status"]<500 and c.get("json_keys") is not None: break
        item={"base":root,"checks":checks}
        model_check=next((c for c in checks if c["url"].endswith("/v1/models") and c.get("status")==200),None)
        if model_check:
            try:
                with urlopen(Request(root+"/v1/models",headers={"User-Agent":"trading-agent-s10-probe/1"}),timeout=5) as rr:
                    body=json.loads(rr.read(20000).decode("utf-8","replace"))
                models=body.get("data") if isinstance(body,dict) else None
                if isinstance(models,list) and models and isinstance(models[0],dict) and models[0].get("id"):
                    mid=str(models[0]["id"])
                    item["model_ids"]=[str(x.get("id")) for x in models if isinstance(x,dict) and x.get("id")][:20]
                    item["inference_smoke"]=http_post(root+"/v1/chat/completions",{"model":mid,"messages":[{"role":"user","content":"Respond exactly with S10_LIVE_READY and nothing else."}],"temperature":0,"max_tokens":8,"stream":False})
            except Exception as e: item["model_discovery_error"]=type(e).__name__
        result["local_interfaces"].append(item)
    result["memory"]={}
    r=ps(r'''$o=Get-CimInstance Win32_OperatingSystem -EA SilentlyContinue; if($o){[ordered]@{total_virtual_mb=[math]::Round($o.TotalVirtualMemorySize/1024,1);free_virtual_mb=[math]::Round($o.FreeVirtualMemory/1024,1);total_physical_mb=[math]::Round($o.TotalVisibleMemorySize/1024,1);free_physical_mb=[math]::Round($o.FreePhysicalMemory/1024,1)}}|ConvertTo-Json -Compress''')
    data=parse_json(r.stdout if r else ""); result["memory"]=data if isinstance(data,dict) else {}
    if any(x.get("inference_smoke",{}).get("status")==200 and x.get("inference_smoke",{}).get("marker_present") for x in result["local_interfaces"]): result["status"]="S10_INFERENCE_READY"
    elif any(x.get("version_returncode")==0 for x in result["cli"]): result["status"]="S10_CLI_REACHABLE"
    elif result["local_interfaces"] or processes: result["status"]="S10_INTERFACE_DISCOVERED_NOT_FULLY_VERIFIED"
    else: result["status"]="S10_NOT_DISCOVERED"
    print(json.dumps(result,ensure_ascii=False,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
