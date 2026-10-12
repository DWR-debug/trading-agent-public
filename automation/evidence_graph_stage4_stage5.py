"""Stage 4/5 Evidence Knowledge Graph and hypothesis convergence engine."""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
CAND_RE=re.compile(r"\b(?:Q\d{2,4}(?::[A-Z0-9]+)?|I\d{2,4}|H\d{2,3}-P\d)\b")
FP_RE=re.compile(r"\b[0-9a-f]{64}\b",re.I)
STOP={"the","and","for","with","from","that","this","candidate","state","public","source","historical","information","market","data","event","filing","issuer","security","deterministic","only","after","before","through","using","into","same","different","distinct","research","evidence","receipt","status"}

def norm(s):
    s=re.sub(r"https?://"," URL ",str(s or "").lower())
    s=re.sub(r"[^a-z0-9:_-]+"," ",s)
    return " ".join(x for x in s.split() if x not in STOP)

def toks(s): return {x for x in norm(s).split() if len(x)>=3}
def sha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def flat(v,path=""):
    out=[]
    if isinstance(v,dict):
        for k,x in v.items(): out.extend(flat(x,path+"/"+str(k)))
    elif isinstance(v,list):
        for i,x in enumerate(v): out.extend(flat(x,path+"/"+str(i)))
    elif isinstance(v,str): out.append((path,v))
    return out

def urls(strings):
    out=set()
    for _,s in strings: out.update(re.findall(r"https?://[^\s\"'<>]+",s))
    return sorted(out)

def cands(strings):
    out=set()
    for _,s in strings: out.update(CAND_RE.findall(s))
    return sorted(out)

def load_json(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return None

def files():
    out=[]
    for base in ("research/evidence","research/governance","research/candidates","research/preregistrations"):
        p=ROOT/base
        if p.exists(): out.extend(x for x in p.rglob("*.json") if x.is_file())
    return sorted(out)

def candidate_inventory():
    """Load a deterministic union of current contracts, legacy waves and discovery seeds.

    The current canonical contract wins on duplicate IDs. Older inventories remain
    visible for overlap analysis but never gain dispatch or authorization status.
    """
    primary = ROOT / "research/candidates/orthogonal_candidate_specs_2026-10-05.json"
    roots = [ROOT / "research/candidates", ROOT / "research/frontier"]
    paths = ([primary] if primary.is_file() else [])
    paths.extend(
        p for root in roots if root.exists()
        for p in sorted(root.rglob("*.json"))
        if p != primary
    )
    inventory = {}
    for path in paths:
        obj = load_json(path)
        if not isinstance(obj, dict):
            continue
        records = []
        for key in ("candidates", "candidate_seeds"):
            value = obj.get(key)
            if isinstance(value, list):
                records.extend(value)
        for row in records:
            if not isinstance(row, dict):
                continue
            cid = str(row.get("id") or row.get("code") or "").strip()
            if not cid or not any(row.get(k) for k in ("name", "mechanism", "hypothesis")):
                continue
            sources = row.get("sources") or row.get("source_evidence") or row.get("information_channel") or []
            if isinstance(sources, (dict, list, tuple)):
                sources = json.dumps(sources, sort_keys=True, ensure_ascii=False)
            source = path.relative_to(ROOT).as_posix()
            if cid not in inventory:
                inventory[cid] = {
                    "id": cid,
                    "name": row.get("name", ""),
                    "mechanism": row.get("mechanism") or row.get("hypothesis") or row.get("name", ""),
                    "economic_relation": row.get("economic_relation") or row.get("construction") or row.get("purpose", ""),
                    "information_channel": str(sources),
                    "event_clock": row.get("event_clock") or row.get("clock") or "",
                    "state_transition": row.get("state_transition") or row.get("next_gate") or "",
                    "identity_basis": row.get("identity_basis") or row.get("exposure_mapping") or "",
                    "description": row.get("description") or row.get("why_distinct") or row.get("name", ""),
                    "purpose": row.get("purpose", ""),
                    "inventory_source": source,
                    "inventory_sources": [source],
                }
            elif source not in inventory[cid]["inventory_sources"]:
                inventory[cid]["inventory_sources"].append(source)
    return inventory


def sig(spec,components):
    fields=[spec.get(k) for k in ("mechanism","economic_relation","information_channel","event_clock","state_transition","identity_basis","description","purpose") if isinstance(spec.get(k),str)]
    nt=set()
    for x in fields: nt |= toks(x)
    domains=set()
    for u in urls(flat(spec)):
        try: domains.add(urlparse(u).netloc.lower())
        except ValueError: pass
    return {"tokens":sorted(nt),"source_domains":sorted(domains),"components":sorted(components.get(str(spec.get("id")),set())),"mechanism_text":" | ".join(fields)}

def jac(a,b):
    u=a|b
    return len(a&b)/len(u) if u else 1.0


def observed_jaccard(a,b):
    """Return a similarity only when both candidates provide this dimension.

    Empty metadata is missing evidence, not proof that two candidates match or
    are disjoint. Stage 5 must fail closed when a comparison dimension is absent.
    """
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def compare_signatures(sa,sb):
    weights={"tokens":.60,"components":.25,"source_domains":.15}
    similarities={
        "tokens":observed_jaccard(set(sa.get("tokens") or []),set(sb.get("tokens") or [])),
        "components":observed_jaccard(set(sa.get("components") or []),set(sb.get("components") or [])),
        "source_domains":observed_jaccard(set(sa.get("source_domains") or []),set(sb.get("source_domains") or [])),
    }
    observed={k:v for k,v in similarities.items() if v is not None}
    complete=len(observed)==len(weights)
    denominator=sum(weights[k] for k in observed)
    # The partial value is a diagnostic only. It can never classify an
    # incompletely observed pair as orthogonal or fully convergent.
    score=(sum(weights[k]*v for k,v in observed.items())/denominator) if denominator else None
    return {
        "score":score,
        "similarities":similarities,
        "observed_dimensions":sorted(observed),
        "signature_coverage_complete":complete,
    }


def candidate_signature(spec,links):
    """Stable public helper used by Stage 5 unit tests and external diagnostics."""
    normalized=defaultdict(set)
    for cid,values in (links or {}).items():
        normalized[str(cid)].update(str(v) for v in (values or []))
    return sig(spec,normalized)


def jaccard(a,b):
    return jac(set(a),set(b))


def novelty_analysis(candidates):
    rows=[]
    ids=sorted(candidates)
    for a in ids:
        pair_rows=[]
        for b in ids:
            if a==b:
                continue
            comparison=compare_signatures(candidates[a],candidates[b])
            sims=comparison["similarities"]
            pair_rows.append({
                "candidate":b,
                "score":round(comparison["score"],6) if comparison["signature_coverage_complete"] else None,
                "token_jaccard":round(sims["tokens"],6) if sims["tokens"] is not None else None,
                "component_jaccard":round(sims["components"],6) if sims["components"] is not None else None,
                "domain_jaccard":round(sims["source_domains"],6) if sims["source_domains"] is not None else None,
                "observed_dimensions":comparison["observed_dimensions"],
                "signature_coverage_complete":comparison["signature_coverage_complete"],
                "_partial_score":comparison["score"],
            })
        complete=[r for r in pair_rows if r["signature_coverage_complete"]]
        incomplete=[r for r in pair_rows if not r["signature_coverage_complete"]]
        best_row=max(complete,key=lambda r:r["score"]) if complete else None
        best=best_row["score"] if best_row else None
        # One observed high-overlap pair is sufficient to raise a convergence
        # warning. Orthogonality requires complete metadata for every peer.
        if any(r["score"]>=.78 for r in complete):
            cls="POTENTIAL_CONVERGENCE"
        elif incomplete or best is None:
            cls="AMBIGUOUS"
        elif best>=.45:
            cls="AMBIGUOUS"
        else:
            cls="LIKELY_ORTHOGONAL"
        for row in pair_rows:
            row.pop("_partial_score",None)
        ordered=sorted(
            pair_rows,
            key=lambda r:(
                not r["signature_coverage_complete"],
                -(r["score"] if r["score"] is not None else (r["token_jaccard"] if r["token_jaccard"] is not None else -1)),
                r["candidate"],
            ),
        )
        rows.append({
            "candidate":a,
            "max_convergence_score":round(best,6) if best is not None else None,
            "most_overlapping_peer":best_row["candidate"] if best_row else None,
            "novelty_score":round(1-best,6) if best is not None and not incomplete else None,
            "overlap_class":cls,
            "signature_coverage":{
                "required_dimensions":3,
                "complete_peer_comparisons":len(complete),
                "incomplete_peer_comparisons":len(incomplete),
                "peer_comparison_count":len(pair_rows),
                "complete":len(incomplete)==0 and best is not None,
            },
            "top_peers":ordered[:5],
        })
    return rows


def bridge_proposals(candidates):
    out=[];ids=sorted(candidates)
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            sa,sb=candidates[a],candidates[b]
            shared=sorted(set(sa["components"]) & set(sb["components"]))
            mo=jaccard(sa["tokens"],sb["tokens"])
            if shared and mo<.45:
                out.append({"proposal_id":"HYP-"+sha({"a":a,"b":b,"shared":shared})[:16],"type":"shared-structure-different-mechanism",
                            "candidates":[a,b],"shared_components":shared,"mechanism_overlap":round(mo,6),
                            "status":"HYPOTHESIS_PROPOSAL_REVIEW_REQUIRED",
                            "text":"Shared deterministic infrastructure may expose a cross-channel state-transition hypothesis; no composite candidate is created."})
    return out


def build():
    node_map={}; edges=[]; docs=[]; components=defaultdict(set)
    contract=load_json(ROOT/"research/governance/knowledge_relation_graph_contract_2026_10_06.json") or {}
    for x in contract.get("candidate_component_links",[]):
        if isinstance(x,dict) and x.get("candidate") and x.get("component"):
            components[str(x["candidate"])].add(str(x["component"]))

    candidates={}
    for cid, spec in candidate_inventory().items():
        candidates[cid]=sig(spec,components)

    def add_node(nid,typ,**kw):
        row={"id":nid,"type":typ};row.update(kw)
        node_map[nid]=row

    def edge(src,dst,typ,basis,confidence="high",**kw):
        row={"from":src,"to":dst,"type":typ,"basis":basis,"confidence":confidence};row.update(kw);edges.append(row)

    for p in files():
        obj=load_json(p)
        if obj is None: continue
        rel=p.relative_to(ROOT).as_posix(); did="doc:"+rel
        add_node(did,"document",path=rel,source_sha256=sha(obj))
        strings=flat(obj); docs.append((did,obj,strings))
        for cid in cands(strings): edge(did,"candidate:"+cid,"mentions","explicit_candidate_token")
        for fp in set(x.lower() for x in FP_RE.findall(" ".join(s for _,s in strings))):
            add_node("receipt:"+fp,"receipt",fingerprint=fp)
            edge(did,"receipt:"+fp,"mentions","sha256_fingerprint")

        for u in urls(strings):
            try:host=urlparse(u).netloc.lower()
            except ValueError:continue
            if host:
                add_node("source:"+host,"source",host=host)
                edge(did,"source:"+host,"documents_source","explicit_url")

        def walk(v,keys=()):
            if isinstance(v,dict):
                for k,x in v.items():
                    key=str(k)
                    if key=="candidate_component_links" and isinstance(x,list):
                        for lk in x:
                            if isinstance(lk,dict):
                                cid=str(lk.get("candidate") or ""); comp=str(lk.get("component") or "")
                                if cid and comp:
                                    nid="component:"+comp; add_node(nid,"source_component",component=comp)
                                    edge("candidate:"+cid,nid,"reuses_component","knowledge_relation_contract")
                    elif key=="candidate_relations" and isinstance(x,list):
                        for rel in x:
                            if isinstance(rel,dict):
                                src=str(rel.get("from") or rel.get("candidate") or ""); dst=str(rel.get("to") or "")
                                if src and dst:
                                    edge("candidate:"+src,"candidate:"+dst,str(rel.get("edge") or "relates_to"),"knowledge_relation_contract",
                                         scientific_interpretation=rel.get("scientific_interpretation"))
                    elif key=="discovery_motifs" and isinstance(x,list):
                        for motif in x:
                            if isinstance(motif,dict):
                                mid=str(motif.get("id") or sha(motif)[:16]); nid="hypothesis:"+mid
                                add_node(nid,"hypothesis",motif_id=mid,pattern=motif.get("pattern"),rule=motif.get("rule"))
                                for cid in cands(flat(motif.get("examples",[]))): edge(nid,"candidate:"+cid,"motif_applies_to","knowledge_relation_contract")
                    elif key in {"negative_evidence","blocked_by","contradicts","revises","non_overlap_with","corroborates","depends_on","derived_from"}:
                        nid=f"{did}:relation:{key}:{sha({'path':keys,'value':x})[:16]}"
                        add_node(nid,"negative_evidence" if key in {"negative_evidence","blocked_by","contradicts","revises"} else "relation_fact",
                                 field=key,summary=str(x)[:800],document=did)
                        edge(did,nid,"documents_relation_fact","nested_structured_field")
                        for cid in cands(flat(x)): edge(nid,"candidate:"+cid,key,"nested_structured_field")
                    walk(x,keys+(key,))
            elif isinstance(v,list):
                for i,x in enumerate(v): walk(x,keys+(str(i),))
        walk(obj)

        status=str(obj.get("status","")).upper()
        if any(x in status for x in ("BLOCKED","FALSIFIED","FAILED","DATA_INSUFFICIENT","PRUNED")):
            nid=did+":state";add_node(nid,"state",status=status);edge(did,nid,"documents_state","explicit_status")

    for i,a in enumerate(sorted(candidates)):
        for b in sorted(candidates)[i+1:]:
            sa,sb=candidates[a],candidates[b]
            sc=sorted(set(sa["components"])&set(sb["components"]))
            sd=sorted(set(sa["source_domains"])&set(sb["source_domains"]))
            if sc:edge("candidate:"+a,"candidate:"+b,"shares_component","candidate_component_links",components=sc)
            if sd:edge("candidate:"+a,"candidate:"+b,"shares_source_domain","explicit_urls",confidence="medium",domains=sd)

    graph={"schema_version":1,"record_type":"evidence_knowledge_graph","stage":"STAGE_4","status":"METADATA_ONLY",
           "input_document_count":len(docs),"node_count":len(node_map),"edge_count":len(edges),
           "nodes":sorted(node_map.values(),key=lambda x:x["id"]),"edges":edges,
           "content_fingerprint":sha({"nodes":node_map,"edges":edges}),
           "scientific_boundary":{k:False for k in ("performance_authorized","holdout_selection_allowed","ranking_allowed","parameter_search_allowed","threshold_search_allowed","horizon_search_allowed","promotion_allowed","live_execution_allowed")}}

    nov=novelty_analysis(candidates)
    ids=sorted(candidates)
    bridges=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            sa,sb=candidates[a],candidates[b]; shared=sorted(set(sa["components"])&set(sb["components"])); mo=jac(set(sa["tokens"]),set(sb["tokens"]))
            if shared and mo<.45:
                bridges.append({"proposal_id":"HYP-"+sha({"a":a,"b":b,"shared":shared})[:16],"type":"shared-structure-different-mechanism",
                                "candidates":[a,b],"shared_components":shared,"mechanism_overlap":round(mo,6),
                                "status":"HYPOTHESIS_PROPOSAL_REVIEW_REQUIRED",
                                "text":"Shared deterministic infrastructure may expose a cross-channel state-transition hypothesis; no composite candidate is created."})
    negatives=[e for e in edges if e["type"] in {"contradicts","revises","blocked_by"} or e.get("field") in {"contradicts","revises","blocked_by"}]
    return graph,nov,bridges,negatives,candidates

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=("relation","negative","novelty","full"),default="full");ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    graph,nov,bridges,negatives,candidates=build()
    if a.mode=="relation":r=graph
    elif a.mode=="negative":r={"schema_version":1,"record_type":"evidence_graph_negative_revision_audit","status":"METADATA_ONLY","negative_edges":negatives,"negative_edge_count":len(negatives),"input_fingerprint":graph["content_fingerprint"]}
    elif a.mode=="novelty":r={"schema_version":1,"record_type":"hypothesis_novelty_convergence_audit","stage":"STAGE_5","status":"REVIEW_ONLY","candidate_count":len(candidates),"pairs_analyzed":len(candidates)*(len(candidates)-1)//2,"results":nov,"input_fingerprint":graph["content_fingerprint"],"scientific_authority":False}
    else:r={"schema_version":1,"record_type":"stage4_stage5_synthesis","status":"METADATA_ONLY_REVIEW_REQUIRED","graph":graph,"novelty_convergence":nov,"bridge_hypothesis_proposals":bridges,"negative_revision_edges":negatives,
            "summary":{"candidates":len(candidates),"nodes":graph["node_count"],"edges":graph["edge_count"],"proposals":len(bridges),"negative_revision_edges":len(negatives)},
            "safety":{"performance":False,"holdout_selection":False,"ranking":False,"tuning":False,"promotion":False,"live_execution":False}}
    r["receipt_fingerprint"]=sha(r);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"mode":a.mode,"record_type":r["record_type"],"fingerprint":r["receipt_fingerprint"],"summary":r.get("summary",{})},sort_keys=True))

if __name__=="__main__":main()
