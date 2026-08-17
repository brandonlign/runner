#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from typing import Any
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader

YEARS=(2013,2014); COMP='catalogue HDBSCAN'; MAP_SHA='f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778'
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def canonical(ids): return hashlib.sha256(('\n'.join(sorted(ids))+'\n').encode()).hexdigest()
def f1(a:set[str],b:set[str])->float:
    if not a or not b:return 0.0
    i=len(a&b); return 0.0 if not i else 2.0*i/(len(a)+len(b))
def dump(p,o):
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); Path(p).write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for y in YEARS:
        ap.add_argument(f'--csv-{y}',type=Path,required=True); ap.add_argument(f'--hdbscan-{y}-dir',type=Path,required=True)
    ap.add_argument('--mapping-audit',type=Path,required=True); ap.add_argument('--prepare-dir',type=Path,required=True); ap.add_argument('--candidate-dir',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); req(sha(a.mapping_audit)==MAP_SHA,'mapping identity'); mapping=load(a.mapping_audit)
    cp=a.candidate_dir/'candidate_primary_output.json'; cmp=a.candidate_dir/'candidate_source_manifest.json'; cand=load(cp); req(cand['method']=='fixed-scale TopoModal flagship' and cand['truth_accessed'] is False,'candidate identity'); fams=cand['families']; req(len(fams)==cand['family_count']==1455,'candidate count')
    panels=[]
    for y in YEARS:
        rp=a.prepare_dir/f'hdbscan_{y}.json'; rows=load(rp); ids=[str(r['id']) for r in rows]; rs=set(ids); req(len(rs)==len(ids),'row dupes')
        hd=getattr(a,f'hdbscan_{y}_dir'); hp=hd/'comparator_primary_output.json'; hmp=hd/'comparator_source_manifest.json'; hdb=load(hp); req(hdb['method']==COMP and hdb['year']==y and hdb['truth_accessed'] is False,'HDB identity')
        tf={'year':y,'comparator':COMP,'pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_access':False,'pairwise_event_ids_sha256':canonical(ids),'orbittrace_primary_output_sha256':sha(cp),'comparator_primary_output_sha256':sha(hp),'orbittrace_source_manifest_sha256':sha(cmp),'comparator_source_manifest_sha256':sha(hmp)}
        csv=getattr(a,f'csv_{y}').read_bytes(); truth,audit=truth_reader.parse_truth_after_freeze(csv,year=y,comparator=COMP,requested_event_ids=ids,mapping_audit=mapping,mapping_audit_sha256=MAP_SHA,pretruth_freeze=tf,id_prefix=f'SNT{y}')
        cnt=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in cnt.items() if n>=4); truth_sets={lab:{eid for eid in ids if truth[eid]==lab} for lab in labels}
        topo=[]
        for fam in fams:
            s=set(str(e) for e in fam['event_ids'])&rs
            if not s: continue
            topo.append((int(fam['rank']),str(fam['family_id']),s,bool(fam['is_root']),int(fam['member_count']),fam.get('creation_prominence'),fam.get('prominence_span'),fam.get('mean_density'),fam.get('peak_density')))
        hfamilies=[]
        for fam in hdb['families']:
            s=set(str(e) for e in fam['member_ids'])&rs
            if s: hfamilies.append((str(fam['family_id']),s))
        per=[]
        for lab in labels:
            ts=truth_sets[lab]
            best_t=max(((f1(ts,s),rank,fid,len(s),is_root,creation,span,mean,peak) for rank,fid,s,is_root,_,creation,span,mean,peak in topo),default=(0,None,None,0,None,None,None,None,None))
            best_h=max(((f1(ts,s),fid,len(s)) for fid,s in hfamilies),default=(0,None,0))
            qualifying=[(rank,f1(ts,s),fid,len(s)) for rank,fid,s,*_ in topo if f1(ts,s)>0.5]
            first=min(qualifying,key=lambda z:z[0]) if qualifying else None
            per.append({'label':lab,'truth_rows':len(ts),'topomodal_best_f1':best_t[0],'topomodal_best_rank':best_t[1],'topomodal_best_family':best_t[2],'topomodal_best_year_member_count':best_t[3],'topomodal_best_is_root':best_t[4],'topomodal_best_creation_prominence':best_t[5],'topomodal_best_prominence_span':best_t[6],'topomodal_best_mean_density':best_t[7],'topomodal_best_peak_density':best_t[8],'topomodal_first_rank_f1_gt_0_5':None if first is None else first[0],'topomodal_first_f1_gt_0_5':None if first is None else first[1],'hdbscan_best_f1':best_h[0],'hdbscan_best_family':best_h[1],'hdbscan_best_member_count':best_h[2]})
        hdb_recover=[x for x in per if x['hdbscan_best_f1']>0.5]; generator_covers=[x for x in hdb_recover if x['topomodal_best_f1']>0.5]; hdb_only=[x for x in hdb_recover if x['topomodal_best_f1']<=0.5]
        late=[x for x in generator_covers if (x['topomodal_first_rank_f1_gt_0_5'] or 10**9)>int(hdb['retained_family_count'])]
        panel={'year':y,'event_count':len(ids),'topomodal_candidate_with_year_members':len(topo),'hdbscan_family_count':len(hfamilies),'eligible_labels':len(labels),'hdbscan_independent_recoverable_f1_gt_0_5':len(hdb_recover),'topomodal_all_candidate_recoverable_f1_gt_0_5':sum(x['topomodal_best_f1']>0.5 for x in per),'hdbscan_recoverable_also_present_anywhere_topomodal':len(generator_covers),'hdbscan_recoverable_absent_from_topomodal':len(hdb_only),'hdbscan_recoverable_present_only_after_budget':len(late),'hdbscan_only_labels':[x['label'] for x in hdb_only],'late_labels':[{'label':x['label'],'first_topomodal_rank':x['topomodal_first_rank_f1_gt_0_5'],'best_topomodal_f1':x['topomodal_best_f1'],'hdbscan_best_f1':x['hdbscan_best_f1']} for x in sorted(late,key=lambda z:z['topomodal_first_rank_f1_gt_0_5'])],'per_label':per,'truth_audit':audit}
        dump(a.output/f'diagnostic_{y}.json',panel); panels.append(panel)
    result={'schema':'ORBITTRACE_TOPOMODAL_FULL_RECOVERABILITY_DIAGNOSTIC_V1','scientific_role':'EXPOSED_SONOTACO_DEVELOPMENT_DIAGNOSTIC_ONLY','panels':panels,'protected_target_access':False,'method_mutation':False}; rh=dump(a.output/'DIAGNOSTIC_RESULT.json',result); print(json.dumps({'result_sha256':rh,'panels':[{k:p[k] for k in ['year','hdbscan_independent_recoverable_f1_gt_0_5','topomodal_all_candidate_recoverable_f1_gt_0_5','hdbscan_recoverable_also_present_anywhere_topomodal','hdbscan_recoverable_absent_from_topomodal','hdbscan_recoverable_present_only_after_budget']} for p in panels]},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
