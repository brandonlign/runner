#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
YEARS=(2013,2014); METHOD='OrbitTrace TopoModal Predictive Tree Cut v1'; LIT='catalogue HDBSCAN'
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def dump(p,o):
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); Path(p).write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--prepare-dir',type=Path,required=True); ap.add_argument('--selector-dir',type=Path,required=True); ap.add_argument('--hdbscan-2013-dir',type=Path,required=True); ap.add_argument('--hdbscan-2014-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    sp=a.selector_dir/'selector_primary_output.json'; smp=a.selector_dir/'selector_source_manifest.json'; s=load(sp); sm=load(smp)
    req(s.get('method')==METHOD and s.get('truth_accessed') is False and s.get('target_information_access') is False,'selector identity/access')
    req(s.get('target_region_events_accessed') is False and s.get('post_result_parameter_search') is False,'selector firewall')
    req(sm.get('truth_accessed') is False and sm.get('target_information_access') is False,'selector manifest')
    panels={int(p['year']):p for p in s['panels']}; req(set(panels)==set(YEARS),'selector years')
    hdirs={2013:a.hdbscan_2013_dir,2014:a.hdbscan_2014_dir}; frozen=[]
    for y in YEARS:
        p=panels[y]; cs=p['candidates']; req(len(cs)==int(p['selected_candidate_count']) and cs,'selector candidates')
        req([int(c['rank']) for c in cs]==list(range(1,len(cs)+1)),'selector ranks')
        req(all(float(c['heldout_predictive_gain'])>0 for c in cs),'nonpositive selected gain')
        owner=set()
        for c in cs:
            ids=set(map(str,c['event_ids'])); req(len(ids)==int(c['member_count']),'selector member count'); req(owner.isdisjoint(ids),'selector overlap'); owner.update(ids)
        g=p['graph_summary']; req(int(g['physical_edge_count'])>0 and int(g['training_edge_count'])>0 and int(g['heldout_edge_count'])>0,'graph split empty')
        rp=a.prepare_dir/f'hdbscan_{y}.json'; rows=load(rp); ids=[str(r['id']) for r in rows]; req(len(ids)==len(set(ids)),'row dupes'); idsha=hashlib.sha256(('\n'.join(sorted(ids))+'\n').encode()).hexdigest()
        hd=hdirs[y]; hp=hd/'comparator_primary_output.json'; hmp=hd/'comparator_source_manifest.json'; hsp=hd/'comparator_pretruth_summary.json'; h=load(hp); hm=load(hmp); hs=load(hsp)
        req(h.get('method')==LIT and int(h.get('year',-1))==y and h.get('truth_accessed') is False,'HDB identity'); req(hm.get('target_information_access') is False and hm.get('truth_labels_accepted') is False,'HDB manifest')
        B=int(h.get('retained_family_count',-1)); req(B==len(h['families']) and B>0,'HDB budget'); req(len(cs)>=B,'selector capacity below HDB budget')
        req(hs.get('primary_output_sha256')==sha(hp) and hs.get('source_manifest_sha256')==sha(hmp),'HDB hash mismatch')
        frozen.append({'year':y,'event_count':len(ids),'event_ids_sha256':idsha,'rows_json_sha256':sha(rp),'selector_primary_output_sha256':sha(sp),'selector_source_manifest_sha256':sha(smp),'selector_selected_candidate_count':len(cs),'hdbscan_primary_output_sha256':sha(hp),'hdbscan_source_manifest_sha256':sha(hmp),'hdbscan_pretruth_summary_sha256':sha(hsp),'hdbscan_family_budget':B})
    f={'schema':'ORBITTRACE_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_HDBSCAN_PRETRUTH_FREEZE','method':METHOD,'literature_comparator':LIT,'pretruth_outputs_frozen':True,'panels':frozen,'blind_exclusion':[20.0,55.0],'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    fs=dump(a.output/'PRETRUTH_FREEZE.json',f); print(json.dumps({'verdict':'PASS_TOPOMODAL_PREDICTIVE_TREE_CUT_V1_HDBSCAN_PRETRUTH_FREEZE','freeze_sha256':fs,'panels':frozen},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
