"""Stage 4/5 deterministic Evidence Knowledge Graph + novelty/convergence engine.

No market outcomes. No performance/ranking/selection. Graph and hypothesis outputs
are control-plane research artifacts only.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_RE = re.compile(r"\b(?:Q\d{2,4}(?::[A-Z0-9]+)?|I\d{2,4}|H\d{2,3}-P\d)\b")
FINGERPRINT_RE = re.compile(r"\b[0-9a-f]{64}\b", re.I)
STOP = {
    "the","and","for","with","from","that","this","candidate","state","public",
    "source","historical","information","market","data","event","filing","issuer",
    "security","deterministic","only","after","before","through","using","into",
    "same","different","distinct","research","evidence","receipt","status"
}
FORBIDDEN_KEYS = {
    "performance": True, "performance_authorization": True, "holdout_selection": True,
    "ranking": True, "tuning": True, "promotion": True, "live_execution": True
}

def canon_text(value) -> str:
    s = str(value or "").lower()
    s = re.sub(r"https?://", " URL ", s)
    s = re.sub(r"[^a-z0-9:_-]+", " ", s)
    return " ".join(x for x in s.split() if x not in STOP)

def tokens(value) -> set[str]:
    return {x for x in canon_text(value).split() if len(x) >= 3}

def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def iter_files() -> list[Path]:
    files=[]
    for root in ("research/evidence","research/governance","research/candidates","research/preregistrations"):
        p=ROOT/root
        if p.exists(): files.extend(x for x in p.rglob("*.json") if x.is_file())
    return sorted(files)

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def safe_flags(obj) -> bool:
    for k,v in FORBIDDEN_KEYS.items():
        if obj.get(k) is True:
            return False
    sf=obj.get("scientific_boundary")
    if isinstance(sf,dict):
        if any(sf.get(k) is True for k in ("performance_authorized","holdout_selection_allowed","ranking_allowed","parameter_search_allowed","threshold_search_allowed","horizon_search_allowed","promotion_allowed","live_execution_allowed")):
            return False
    return True

def flatten_strings(value, prefix=""):
    out=[]
    if isinstance(value,dict):
        for k,v in value.items():
            out.extend(flatten_strings(v, prefix+"/"+str(k)))
    elif isinstance(value,list):
        for i,v in enumerate(value):
            out.extend(flatten_strings(v, prefix+f"/{i}"))
    elif isinstance(value,str):
        out.append((prefix,value))
    return out

def extract_urls(strings):
    urls=[]
    for _,s in strings:
        urls.extend(re.findall(r"https?://[^\s\"\'<>]+",s))
    return sorted(set(urls))

def extract_candidates(strings):
    out=set()
    for _,s in strings: out.update(CANDIDATE_RE.findall(s))
    return sorted(out)

def candidate_signature(spec:dict, links_by_candidate:dict[str,set[str]]):
    fields=[]
    for k in ("mechanism","economic_relation","information_channel","event_clock","state_transition","identity_basis","description","purpose"):
        if isinstance(spec.get(k),str): fields.append(spec[k])
    nested = spec.get("mechanism_definition")
    if isinstance(nested,dict):
        fields += [str(v) for v in nested.values() if isinstance(v,str)]
    sig_tokens=set()
    for x in fields: sig_tokens |= tokens(x)
    sources=set()
    for u in extract_urls(flatten_strings(spec)):
        try: sources.add(urlparse(u).netloc.lower())
        except ValueError: pass
    return {
        "tokens":sorted(sig_tokens),
        "source_domains":sorted(sources),
        "components":sorted(links_by_candidate.get(str(spec.get("id")),set())),
        "mechanism_text":" | ".join(fields),
    }

def jaccard(a:set[str],b:set[str])->float:
    if not a and not b:return 1.0
    return len(a&b)/len(a|b) if (a|b) else 0.0

def build_relation_graph():
    nodes=[]; edges=[]; docs=[]; candidates={}
    contract_nodes={}
    candidate_specs_path=ROOT/"research/candidates/orthogonal_candidate_specs_2026-10-05.json"
    candidate_specs=load_json(candidate_specs_path) or {}
    specs=candidate_specs.get("candidates",[]) if isinstance(candidate_specs,dict) else []
    links_by_candidate=defaultdict(set)
    contract=load_json(ROOT/"research/governance/knowledge_relation_graph_contract_2026_10_06.json") or {}
    for link in contract.get("candidate_component_links",[]):
        if link.get("candidate") and link.get("component"):
            links_by_candidate[str(link["candidate"])].add(str(link["component"]))
    for spec in specs:
        cid=str(spec.get("id") or "")
        if cid:candidates[cid]=candidate_signature(spec,links_by_candidate)
    for path in iter_files():
        obj=load_json(path)
        if obj is None: continue
        rel=path.relative_to(ROOT).as_posix()
        strings=flatten_strings(obj)
        doc_id="doc:"+rel
        nodes.append({"id":doc_id,"type":"document","path":rel,"source_sha256":sha(obj)})
        docs.append((doc_id,obj,strings,rel))
        for cid in extract_candidates(strings):
            edges.append({"from":doc_id,"to":"candidate:"+cid,"type":"mentions","basis":"explicit_candidate_token","confidence":"high"})
        for fp in sorted(set(FINGERPRINT_RE.findall(" ".join(s for _,s in strings)))):
            edges.append({"from":doc_id,"to":"receipt:"+fp.lower(),"type":"mentions","basis":"sha256_fingerprint","confidence":"high"})
    for cid in candidates:
        nodes.append({"id":"candidate:"+cid,"type":"candidate","signature":candidates[cid]})
    for doc_id,obj,strings,rel in docs:
        urls=extract_urls(strings)
        for u in urls:
            try:host=urlparse(u).netloc.lower()
            except ValueError:continue
            nodes.append({"id":"source:"+host,"type":"source","host":host})
            edges.append({"from":doc_id,"to":"source:"+host,"type":"documents_source","basis":"explicit_url","confidence":"high"})
        # explicit relation vocab
        for key,edge_type in (("depends_on","depends_on"),("reuses_component","reuses_component"),("corroborates","corroborates"),("contradicts","contradicts"),("revises","revises"),("blocked_by","blocked_by"),("non_overlap_with","non_overlap_with"),("derived_from","derived_from")):
            val=obj.get(key)
            if isinstance(val,list):
                for item in val:
                    if isinstance(item,str):
                        for cid in extract_candidates([(key,item)]):
                            edges.append({"from":doc_id,"to":"candidate:"+cid,"type":edge_type,"basis":"explicit_structured_field","confidence":"high"})
        neg=obj.get("negative_evidence")
        if neg is not None:
            nodes.append({"id":doc_id+":negative","type":"negative_evidence","document":doc_id,"summary":str(neg)[:500]})
            edges.append({"from":doc_id,"to":doc_id+":negative","type":"documents_negative_evidence","basis":"explicit_negative_evidence_field","confidence":"high"})
        status=str(obj.get("status","")).upper()
        if any(x in status for x in ("BLOCKED","FALSIFIED","FAILED","DATA_INSUFFICIENT","PRUNED")):
            nodes.append({"id":doc_id+":state","type":"state","status":status})
            edges.append({"from":doc_id,"to":doc_id+":state","type":"documents_state","basis":"explicit_status","confidence":"high"})
    # Candidate shared source / component / clock edges are deterministic research relations.
    candidate_nodes=sorted(candidates)
    for i,a in enumerate(candidate_nodes):
        for b in candidate_nodes[i+1:]:
            sa,sb=candidates[a],candidates[b]
            shared_components=sorted(set(sa["components"])&set(sb["components"]))
            shared_domains=sorted(set(sa["source_domains"])&set(sb["source_domains"]))
            if shared_components:
                edges.append({"from":"candidate:"+a,"to":"candidate:"+b,"type":"shares_component","basis":"candidate_component_links","components":shared_components,"confidence":"high"})
            if shared_domains:
                edges.append({"from":"candidate:"+a,"to":"candidate:"+b,"type":"shares_source_domain","basis":"explicit_urls","domains":shared_domains,"confidence":"medium"})
    return nodes,edges,docs,candidates

def novelty_analysis(candidates):
    out=[]
    ids=sorted(candidates)
    for i,a in enumerate(ids):
        best=0.0; best_peer=None; peer_rows=[]
        for b in ids:
            if a==b: continue
            s=candidates[a]; t=candidates[b]
            tok=jaccard(set(s["tokens"]),set(t["tokens"]))
            comp=jaccard(set(s["components"]),set(t["components"]))
            dom=jaccard(set(s["source_domains"]),set(t["source_domains"]))
            score=0.60*tok+0.25*comp+0.15*dom
            peer_rows.append((b,score,tok,comp,dom))
            if score>best:best=score;best_peer=b
        if best>=0.78: cls="POTENTIAL_CONVERGENCE"
        elif best>=0.45: cls="AMBIGUOUS"
        else: cls="LIKELY_ORTHOGONAL"
        out.append({
            "candidate":a,"max_convergence_score":round(best,6),"most_overlapping_peer":best_peer,
            "novelty_score":round(1.0-best,6),"overlap_class":cls,
            "signature_token_count":len(candidates[a]["tokens"]),
            "top_peers":[{"candidate":p,"score":round(sc,6),"token_jaccard":round(t,6),"component_jaccard":round(c,6),"domain_jaccard":round(d,6)}
                         for p,sc,t,c,d in sorted(peer_rows,key=lambda x:-x[1])[:5]]
        })
    return out

def bridge_proposals(candidates):
    proposals=[]
    ids=sorted(candidates)
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            sa,sb=candidates[a],candidates[b]
            shared=set(sa["components"])&set(sb["components"])
            token_overlap=jaccard(set(sa["tokens"]),set(sb["tokens"]))
            if shared and token_overlap < 0.45:
                proposals.append({
                    "proposal_id":"HYP-"+sha({"a":a,"b":b,"shared":sorted(shared)})[:16],
                    "type":"shared-structure-different-mechanism",
                    "candidates":[a,b],
                    "shared_components":sorted(shared),
                    "mechanism_overlap":round(token_overlap,6),
                    "status":"HYPOTHESIS_PROPOSAL_REVIEW_REQUIRED",
                    "text":"Shared deterministic infrastructure may expose a cross-channel state-transition hypothesis; no composite candidate is created."
                })
    return proposals

def mode_output(mode:str):
    nodes,edges,docs,candidates=build_relation_graph()
    graph={"schema_version":"1.0","record_type":"evidence_knowledge_graph","stage":"STAGE_4","status":"METADATA_ONLY",
           "input_document_count":len(docs),"node_count":len(nodes),"edge_count":len(edges),
           "nodes":nodes,"edges":edges,
           "content_fingerprint":sha({"nodes":nodes,"edges":edges}),
           "scientific_boundary":{k:False for k in ("performance_authorized","holdout_selection_allowed","ranking_allowed","parameter_search_allowed","threshold_search_allowed","horizon_search_allowed","promotion_allowed","live_execution_allowed")}}
    novelty=novelty_analysis(candidates)
    bridges=bridge_proposals(candidates)
    negatives=[e for e in edges if e["type"] in {"contradicts","revises","blocked_by"}]
    if mode=="relation": return graph
    if mode=="negative": return {"schema_version":"1.0","record_type":"evidence_graph_negative_revision_audit","status":"METADATA_ONLY","negative_edges":negatives,"negative_edge_count":len(negatives),"input_fingerprint":graph["content_fingerprint"]}
    if mode=="novelty": return {"schema_version":"1.0","record_type":"hypothesis_novelty_convergence_audit","stage":"STAGE_5","status":"REVIEW_ONLY","candidate_count":len(candidates),"pairs_analyzed":len(candidates)*(len(candidates)-1)//2,"results":novelty,"input_fingerprint":graph["content_fingerprint"],"scientific_authority":False}
    return {"schema_version":"1.0","record_type":"stage4_stage5_synthesis","status":"METADATA_ONLY_REVIEW_REQUIRED","graph":graph,"novelty_convergence":novelty,"bridge_hypothesis_proposals":bridges,
            "negative_revision_edges":negatives,"summary":{"candidates":len(candidates),"nodes":len(nodes),"edges":len(edges),"proposals":len(bridges)},
            "safety":{"performance":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("relation","negative","novelty","full"),default="full")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=mode_output(args.mode)
    result["receipt_fingerprint"]=sha(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"mode":args.mode,"record_type":result.get("record_type"),"fingerprint":result["receipt_fingerprint"],
                      "summary":result.get("summary",{"edges":result.get("edge_count"),"negatives":result.get("negative_edge_count"),"pairs":result.get("pairs_analyzed")})},ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
