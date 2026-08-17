#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader
YEARS=(2013,2014); METHOD='OrbitTrace Adaptive Density Ascent v1'; LIT='catalogue HDBSCAN'
EVAL_SHA='cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c'; MAP_SHA='f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778'
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def dump(p,o):
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); Path(p).write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def loadmod(p,n):
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,'module load'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def candidate(payload):
    req(payload.get('method')==METHOD,'candidate method'); out=[]; order=[]; seen=set()
    for rank,f in enumerate(payload['families'],1):
        fid=str(f['family_id']); req(fid not in seen and int(f['rank'])==rank,'candidate order'); ids=[str(x) for x in f['event_ids']]; req(ids and len(ids)==len(set(ids)),'candidate ids'); seen.add(fid); order.append(fid); out.append({'family_id':fid,'event_ids':ids})
    req(len(out)==int(payload['family_count']),'candidate count'); return order,out
def literature(payload):
    req(payload.get('method')==LIT,'HDB method'); out=[]; seen=set()
    for f in payload['families']:
        fid=str(f['family_id']); req(fid not in seen,'HDB duplicate'); ids=[str(x) for x in f['member_ids']]; req(ids and len(ids)==len(set(ids)),'HDB ids'); seen.add(fid); out.append({'family_id':fid,'event_ids':ids})
    req(len(out)==int(payload['retained_family_count']),'HDB count'); return out
def metrics(truth,row_ids,fams):
    rs=set(row_ids); req(set(truth)==rs,'truth universe'); counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4); req(labels,'no labels'); shower={lab:{e for e in row_ids if truth[e]==lab} for lab in labels}; fs=[set(f['event_ids'])&rs for f in fams]; mat=np.zeros((len(labels),len(fs)),dtype=np.float64)
    for i,lab in enumerate(labels):
        for j,f in enumerate(fs):
            if f:
                inter=len(shower[lab]&f)
                if inter: mat[i,j]=2.0*inter/(len(shower[lab])+len(f))
    a=np.zeros(len(labels),dtype=np.float64)
    if mat.shape[1]: rr,cc=linear_sum_assignment(-mat); a[rr]=mat[rr,cc]
    return {'eligible_known_shower_count':len(labels),'family_budget':len(fams),'macro_f1':float(np.mean(a)),'recovered_f1_gt_0_5':int(np.sum(a>0.5)),'matched_positive_f1_count':int(np.sum(a>0.0)),'assigned_f1_by_label':{labels[i]:float(a[i]) for i in range(len(labels))}}
def main():
    ap=argparse.ArgumentParser()
    for y in YEARS: ap.add_argument(f'--csv-{y}',type=Path,required=True); ap.add_argument(f'--hdbscan-{y}-dir',type=Path,required=True)
    ap.add_argument('--mapping-audit',type=Path,required=True); ap.add_argument('--evaluator-source',type=Path,required=True); ap.add_argument('--prepare-dir',type=Path,required=True); ap.add_argument('--freeze-file',type=Path,required=True); ap.add_argument('--candidate-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); req(sha(a.mapping_audit)==MAP_SHA and sha(a.evaluator_source)==EVAL_SHA,'evaluator/map drift'); exact=loadmod(a.evaluator_source,'exact_eval'); mapping=load(a.mapping_audit); freeze=load(a.freeze_file); req(freeze['pretruth_outputs_frozen'] is True and freeze['truth_accessed_before_freeze'] is False,'freeze invalid'); fi={int(p['year']):p for p in freeze['panels']}; req(set(fi)==set(YEARS),'years'); csvs={y:getattr(a,f'csv_{y}').read_bytes() for y in YEARS}; mp=a.candidate_dir/'candidate_source_manifest.json'; panels=[]
    for y in YEARS:
        fr=fi[y]; cp=a.candidate_dir/f'candidate_{y}.json'; c=load(cp); order,cf=candidate(c); rp=a.prepare_dir/f'hdbscan_{y}.json'; rows=load(rp); ids=[str(r['id']) for r in rows]
        req(sha(rp)==fr['rows_json_sha256'] and sha(cp)==fr['candidate_primary_output_sha256'] and sha(mp)==fr['candidate_source_manifest_sha256'],'candidate/row drift'); hd=getattr(a,f'hdbscan_{y}_dir'); hp=hd/'comparator_primary_output.json'; hmp=hd/'comparator_source_manifest.json'; hsp=hd/'comparator_pretruth_summary.json'; req(sha(hp)==fr['hdbscan_primary_output_sha256'] and sha(hmp)==fr['hdbscan_source_manifest_sha256'] and sha(hsp)==fr['hdbscan_pretruth_summary_sha256'],'HDB drift'); hf=literature(load(hp)); B=len(hf); req(B==int(fr['hdbscan_family_budget']) and len(cf)>=B,'budget'); cb=cf[:B]
        tf={'year':y,'comparator':LIT,'pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_access':False,'pairwise_event_ids_sha256':fr['event_ids_sha256'],'orbittrace_primary_output_sha256':fr['candidate_primary_output_sha256'],'comparator_primary_output_sha256':fr['hdbscan_primary_output_sha256'],'orbittrace_source_manifest_sha256':fr['candidate_source_manifest_sha256'],'comparator_source_manifest_sha256':fr['hdbscan_source_manifest_sha256']}
        truth,audit=truth_reader.parse_truth_after_freeze(csvs[y],year=y,comparator=LIT,requested_event_ids=ids,mapping_audit=mapping,mapping_audit_sha256=MAP_SHA,pretruth_freeze=tf,id_prefix=f'SNT{y}'); cm=metrics(truth,ids,cb); hm=metrics(truth,ids,hf); req(cm['eligible_known_shower_count']==hm['eligible_known_shower_count'],'truth mismatch'); ex=exact.evaluate_pair({'year':y,'comparator_id':LIT,'row_ids':ids,'row_truth':truth,'candidate_order':order,'candidate_families':cf,'comparator_families':hf}); win=cm['macro_f1']>hm['macro_f1'] and cm['recovered_f1_gt_0_5']>=hm['recovered_f1_gt_0_5']; p={'year':y,'event_count':len(ids),'budget':B,'candidate_capacity':len(cf),'adaptive_density_ascent':cm,'published_hdbscan':hm,'candidate_win':bool(win),'exact_frozen_evaluator_output':ex,'truth_audit':audit}; dump(a.output/f'panel_{y}.json',p); panels.append(p)
    wins=sum(bool(p['candidate_win']) for p in panels); verdict='PASS_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_DEVELOPMENT' if wins==2 else 'FAIL_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_DEVELOPMENT'; result={'schema':'ORBITTRACE_ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_RESULT','scientific_role':'EXPOSED_POST_SELECTION_SONOTACO_2013_2014_DEVELOPMENT','method':METHOD,'literature_comparator':LIT,'panel_wins':wins,'panel_count':2,'verdict':verdict,'panels':panels,'pretruth_freeze_sha256':sha(a.freeze_file),'evaluator_source_sha256':EVAL_SHA,'mapping_audit_sha256':MAP_SHA,'blind_exclusion':[20.0,55.0],'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','truth_access_before_pretruth':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}; rh=dump(a.output/'ADAPTIVE_DENSITY_ASCENT_V1_HDBSCAN_RESULT.json',result); print(json.dumps({'verdict':verdict,'panel_wins':wins,'result_sha256':rh,'panels':[{'year':p['year'],'candidate_macro_f1':p['adaptive_density_ascent']['macro_f1'],'hdbscan_macro_f1':p['published_hdbscan']['macro_f1'],'candidate_recovered':p['adaptive_density_ascent']['recovered_f1_gt_0_5'],'hdbscan_recovered':p['published_hdbscan']['recovered_f1_gt_0_5'],'win':p['candidate_win']} for p in panels]},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
