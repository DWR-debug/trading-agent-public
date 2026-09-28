"""Publish text evidence files with the GitHub Git Data API; no local git required."""
from __future__ import annotations
import argparse, base64, json, os, urllib.request, urllib.error

def api(method, url, payload=None):
    token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token: raise RuntimeError("GH_TOKEN/GITHUB_TOKEN is required")
    data=None if payload is None else json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body=exc.read().decode("utf-8","replace"); raise RuntimeError(f"GitHub API {method} {url} failed: {exc.code}: {body}") from exc

def publish(repository,branch,base_sha,files):
    """Publish immutably while retrying a concurrent fast-forward race."""
    api_root=f"https://api.github.com/repos/{repository}"
    requested_base_sha = base_sha
    for attempt in range(1, 6):
        ref=api("GET",f"{api_root}/git/ref/heads/{branch}")
        current=ref["object"]["sha"]
        if attempt == 1 and current != requested_base_sha:
            raise RuntimeError(
                f"ref moved from {requested_base_sha} to {current}; refusing non-fast-forward publish"
            )
        base_sha = current
        commit=api("GET",f"{api_root}/git/commits/{base_sha}")
        base_tree=commit["tree"]["sha"]
        tree=[]
        for path, local in files:
            raw=open(local,"rb").read()
            try: text=raw.decode("utf-8")
            except UnicodeDecodeError as exc: raise RuntimeError(f"{local} is not UTF-8 text") from exc
            blob=api("POST",f"{api_root}/git/blobs",{"content":text,"encoding":"utf-8"})
            tree.append({"path":path,"mode":"100644","type":"blob","sha":blob["sha"]})
        new_tree=api("POST",f"{api_root}/git/trees",{"base_tree":base_tree,"tree":tree})
        new_commit=api("POST",f"{api_root}/git/commits",{"message":os.environ.get("PUBLISH_MESSAGE","EVIDENCE: publish deterministic research artifacts"),"tree":new_tree["sha"],"parents":[base_sha]})
        try:
            api("PATCH",f"{api_root}/git/refs/heads/{branch}",{"sha":new_commit["sha"],"force":False})
        except RuntimeError as exc:
            if "failed: 422:" not in str(exc) or attempt == 5:
                raise
            continue
        return new_commit["sha"]
    raise RuntimeError("GitHub fast-forward publish exhausted retry budget")

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--repository",required=True); p.add_argument("--branch",default="master"); p.add_argument("--base-sha",required=True); p.add_argument("--file",action="append",default=[],help="repo_path=local_path")
    a=p.parse_args(); files=[]
    for spec in a.file:
        path,sep,local=spec.partition("=")
        if not sep or not path or not local: raise SystemExit("--file must be repo_path=local_path")
        files.append((path,local))
    if not files: raise SystemExit("at least one --file is required")
    print("PUBLISHED_COMMIT:",publish(a.repository,a.branch,a.base_sha,files))