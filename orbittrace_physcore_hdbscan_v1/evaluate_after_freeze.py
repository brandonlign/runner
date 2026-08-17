#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader
MAP='f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778'; EV='cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c'
def req(x,m):
 if not x: raise RuntimeError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def dump(p,o):
 raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();Path(p).write_bytes(raw);return hashlib.sha256(raw).hexdigest()
def metrics(truth,row_ids,fams):
 cnt=Counter(v for v in truth.values() if v!='SPORADIC'); labs=sorted(k for k,n in cnt.items() if n>=4); ss={l:{e for e in row_ids if truth[e]==l} for l in labs}; fs=[set(f['event_ids']) for f in fams]; M=np.zeros((len(labs),len(fs)))
 for i,l in enumerate(labs):
  for j,f in enumerate(fs):
   z=len(ss[l]&f)
   if z:M[i,j]=2*z/(len(ss[l])+len(f))
 a=np.zeros(len(labs))
 if M.shape[1]:r,c=linear_sum_assignment(-M);a[r]=M[r,c]
 return {'eligible_known_shower_count':len(labs),'family_budget':len(fs),'macro_f1':float(np.mean(a)),'recovered_f1_gt_0_5':int(np.sum(a>0.5)),'matched_positive_f1_count':int(np.sum(a>0))}
def main():
 ap=argparse.ArgumentParser();
 for n in ('csv-2013','csv-2014','mapping-audit','evaluator-source','rows','pretruth','freeze','h13','h14','output'):ap.add_argument('--'+n,type=Path,required=True)
 a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);req(sha(a.mapping_audit)==MAP,'mapping changed');req(sha(a.evaluator_source)==EV,'evaluator changed');mapping=load(a.mapping_audit);fr=load(a.freeze);req(fr['pretruth_outputs_frozen'] and not fr['truth_accessed_before_freeze'],'bad freeze');idx={x['year']:x for x in fr['panels']};csvs={2013:a.csv_2013.read_bytes(),2014:a.csv_2014.read_bytes()};panels=[]
 for y,hd in ((2013,a.h13),(2014,a.h14)):
  f=idx[y]; rp=a.rows/f'hdbscan_{y}.json'; rows=load(rp); ids=[str(x['id']) for x in rows]; cp=a.pretruth/f'physcore_{y}.json'; cand=load(cp); hp=hd/'comparator_primary_output.json'; h=load(hp); req(sha(rp)==f['pairwise_rows_json_sha256'] and sha(cp)==f['candidate_output_sha256'] and sha(hp)==f['hdbscan_primary_output_sha256'],'post-freeze change')
  cf=[{'family_id':str(x['family_id']),'event_ids':[str(z) for z in x['event_ids']]} for x in cand['families']]; hf=[{'family_id':str(x['family_id']),'event_ids':[str(z) for z in x['member_ids']]} for x in h['families']];req(len(cf)==len(hf)==f['family_count'],'budget mismatch')
  tf={'year':y,'comparator':'catalogue HDBSCAN','pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_access':False,'pairwise_event_ids_sha256':f['pairwise_event_ids_sha256'],'orbittrace_primary_output_sha256':f['candidate_output_sha256'],'comparator_primary_output_sha256':f['hdbscan_primary_output_sha256'],'orbittrace_source_manifest_sha256':f['candidate_manifest_sha256'],'comparator_source_manifest_sha256':f['hdbscan_source_manifest_sha256']}
  truth,audit=truth_reader.parse_truth_after_freeze(csvs[y],year=y,comparator='catalogue HDBSCAN',requested_event_ids=ids,mapping_audit=mapping,mapping_audit_sha256=MAP,pretruth_freeze=tf,id_prefix=f'SNT{y}')
  cm,hm=metrics(truth,ids,cf),metrics(truth,ids,hf);win=cm['macro_f1']>hm['macro_f1'] and cm['recovered_f1_gt_0_5']>=hm['recovered_f1_gt_0_5'];panels.append({'year':y,'physcore':cm,'published_hdbscan':hm,'win':bool(win),'truth_audit':audit})
 verdict='PASS_PHYSCORE_HDBSCAN_V1_DEVELOPMENT' if all(p['win'] for p in panels) else 'FAIL_PHYSCORE_HDBSCAN_V1_DEVELOPMENT';out={'schema':'ORBITTRACE_PHYSCORE_HDBSCAN_V1_RESULT','scientific_role':'EXPOSED_DEVELOPMENT_ONLY','verdict':verdict,'panels':panels,'pretruth_freeze_sha256':sha(a.freeze),'truth_access_before_pretruth':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False};s=dump(a.output/'RESULT.json',out);print(json.dumps({'verdict':verdict,'result_sha256':s,'panels':panels},indent=2))
if __name__=='__main__':main()
