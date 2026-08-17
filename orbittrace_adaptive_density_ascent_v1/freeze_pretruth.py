#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
YEARS=(2013,2014); METHOD="OrbitTrace Adaptive Density Ascent v1"; LIT="catalogue HDBSCAN"
def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->Any: return json.loads(p.read_text())
def dump(p:Path,o:Any)->str:
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); p.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--prepare-dir',type=Path,required=True); ap.add_argument('--candidate-dir',type=Path,required=True)
    ap.add_argument('--hdbscan-2013-dir',type=Path,required=True); ap.add_argument('--hdbscan-2014-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); mp=a.candidate_dir/'candidate_source_manifest.json'; man=load(mp)
    require(man.get('method')==METHOD and man.get('truth_accessed') is False and man.get('target_information_access') is False,'candidate manifest invalid')
    hdirs={2013:a.hdbscan_2013_dir,2014:a.hdbscan_2014_dir}; panels=[]
    for y in YEARS:
        cp=a.candidate_dir/f'candidate_{y}.json'; c=load(cp); require(c.get('method')==METHOD and int(c.get('year',-1))==y,'candidate identity')
        require(c.get('truth_accessed') is False and c.get('target_information_access') is False and c.get('target_region_events_accessed') is False,'candidate access')
        fams=c.get('families'); require(isinstance(fams,list) and fams and int(c['family_count'])==len(fams),'candidate families'); require([int(f['rank']) for f in fams]==list(range(1,len(fams)+1)),'candidate order')
        s=c['structural_summary']; require(int(s['k'])==14 and int(s['local_root_count'])>1,'candidate structure'); require(float(s['max_reportable_basin_fraction'])<=0.10,'basin collapse')
        rp=a.prepare_dir/f'hdbscan_{y}.json'; rows=load(rp); ids=[str(r['id']) for r in rows]; require(len(ids)==len(set(ids)),'duplicate row IDs'); idsha=hashlib.sha256(("\n".join(sorted(ids))+"\n").encode()).hexdigest()
        hd=hdirs[y]; hp=hd/'comparator_primary_output.json'; hmp=hd/'comparator_source_manifest.json'; hsp=hd/'comparator_pretruth_summary.json'; h=load(hp); hm=load(hmp); hs=load(hsp)
        require(h.get('method')==LIT and int(h.get('year',-1))==y and h.get('truth_accessed') is False,'HDB identity'); require(hm.get('target_information_access') is False and hm.get('truth_labels_accepted') is False,'HDB manifest')
        B=int(h.get('retained_family_count',-1)); require(B==len(h['families']) and B>0,'HDB budget'); require(len(fams)>=B,'candidate capacity')
        require(hs.get('primary_output_sha256')==sha(hp) and hs.get('source_manifest_sha256')==sha(hmp),'HDB hash mismatch')
        panels.append({'year':y,'event_count':len(rows),'event_ids_sha256':idsha,'rows_json_sha256':sha(rp),'candidate_primary_output_sha256':sha(cp),'candidate_source_manifest_sha256':sha(mp),'candidate_family_count':len(fams),'hdbscan_primary_output_sha256':sha(hp),'hdbscan_source_manifest_sha256':sha(hmp),'hdbscan_pretruth_summary_sha256':sha(hsp),'hdbscan_family_budget':B})
    freeze={'schema':'ORBITTRACE_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_PRETRUTH_FREEZE','method':METHOD,'literature_comparator':LIT,'pretruth_outputs_frozen':True,'panels':panels,'blind_exclusion':[20.0,55.0],'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    fs=dump(a.output/'PRETRUTH_FREEZE.json',freeze); print(json.dumps({'verdict':'PASS_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_PRETRUTH_FREEZE','freeze_sha256':fs,'panel_count':len(panels)},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
