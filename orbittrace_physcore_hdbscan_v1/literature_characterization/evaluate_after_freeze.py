#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader
PAIRS=('sugar','dsh');YEARS=(2013,2014);DISPLAY={'sugar':'Sugar','dsh':'Rudawska-Jenniskens D_SH single linkage'}
MAP='f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778';EV='cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c'
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any)->str:
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();p.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
def phys_fams(d):
    out=[]
    for rank,f in enumerate(d['families'],1):
        req(int(f['rank'])==rank,'physcore rank changed');out.append({'family_id':str(f['family_id']),'event_ids':[str(x) for x in f['event_ids']]})
    req(len(out)==int(d['family_count']),'physcore family count changed');return out
def lit_fams(d):
    out=[{'family_id':str(f['family_id']),'event_ids':[str(x) for x in f['member_ids']]} for f in d['families']];req(len(out)==int(d['retained_family_count']),'literature family count changed');return out
def metrics(truth,row_ids,fams):
    req(set(truth)==set(row_ids),'truth universe mismatch');cnt=Counter(v for v in truth.values() if v!='SPORADIC');labs=sorted(k for k,n in cnt.items() if n>=4);ss={l:{e for e in row_ids if truth[e]==l} for l in labs};fs=[set(f['event_ids'])&set(row_ids) for f in fams];M=np.zeros((len(labs),len(fs)))
    for i,l in enumerate(labs):
        for j,f in enumerate(fs):
            z=len(ss[l]&f)
            if z:M[i,j]=2*z/(len(ss[l])+len(f))
    a=np.zeros(len(labs))
    if M.shape[1]:r,c=linear_sum_assignment(-M);a[r]=M[r,c]
    return {'eligible_known_shower_count':len(labs),'family_budget':len(fams),'macro_f1':float(np.mean(a)),'recovered_f1_gt_0_5':int(np.sum(a>0.5)),'matched_positive_f1_count':int(np.sum(a>0))}
def main():
    p=argparse.ArgumentParser();
    for n in ('csv-2013','csv-2014','mapping-audit','evaluator-source','rows','generated','comparators','freeze','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);req(sha(a.mapping_audit)==MAP,'mapping drift');req(sha(a.evaluator_source)==EV,'evaluator drift');mapping=load(a.mapping_audit);fr=load(a.freeze);req(fr['pretruth_outputs_frozen'] and not fr['truth_accessed_before_freeze'],'bad pretruth freeze');req(all(x['exact_membership_equivalence'] for x in fr['transfer_equivalence']),'transfer equivalence failed');idx={(x['pair'],x['year']):x for x in fr['panels']};csvs={2013:a.csv_2013.read_bytes(),2014:a.csv_2014.read_bytes()};truth_reader.COMPARATORS.add(DISPLAY['dsh']);panels=[]
    for pair in PAIRS:
        for y in YEARS:
            f=idx[(pair,y)];rp=a.rows/f'{pair}_{y}.json';rows=load(rp);row_ids=[str(x['id']) for x in rows];cp=a.generated/f'physcore_{pair}_{y}'/f'physcore_{pair}_{y}.json';lp=a.comparators/f'{pair}_{y}'/'comparator_primary_output.json';req(sha(rp)==f['pairwise_rows_json_sha256'] and sha(cp)==f['physcore_output_sha256'] and sha(lp)==f['literature_output_sha256'],'post-freeze drift');cand=phys_fams(load(cp));lit=lit_fams(load(lp));B=len(lit);cand_b=cand[:min(B,len(cand))]
            tf={'year':y,'comparator':DISPLAY[pair],'pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'target_information_access':False,'target_region_access':False,'pairwise_event_ids_sha256':f['pairwise_event_ids_sha256'],'orbittrace_primary_output_sha256':f['physcore_output_sha256'],'comparator_primary_output_sha256':f['literature_output_sha256'],'orbittrace_source_manifest_sha256':f['physcore_manifest_sha256'],'comparator_source_manifest_sha256':f['literature_manifest_sha256']}
            truth,audit=truth_reader.parse_truth_after_freeze(csvs[y],year=y,comparator=DISPLAY[pair],requested_event_ids=row_ids,mapping_audit=mapping,mapping_audit_sha256=MAP,pretruth_freeze=tf,id_prefix=f'SNT{y}')
            cm=metrics(truth,row_ids,cand_b);lm=metrics(truth,row_ids,lit);win=cm['macro_f1']>lm['macro_f1'] and cm['recovered_f1_gt_0_5']>=lm['recovered_f1_gt_0_5'];panels.append({'pair':pair,'literature_method':DISPLAY[pair],'year':y,'literature_budget':B,'physcore_natural_family_count':len(cand),'physcore_evaluated_family_count':len(cand_b),'physcore':cm,'literature':lm,'win':bool(win),'truth_audit':audit})
    verdict='PASS_PHYSCORE_MATCHED_LITERATURE_V1' if all(x['win'] for x in panels) else 'FAIL_PHYSCORE_MATCHED_LITERATURE_V1';out={'schema':'ORBITTRACE_PHYSCORE_MATCHED_LITERATURE_V1_RESULT','scientific_role':'EXPOSED_DEVELOPMENT_ONLY','method':'PhysCore-HDBSCAN v1','direct_published_hdbscan_binding':{'workflow':31988198562,'verdict':'PASS_PHYSCORE_HDBSCAN_V1_DEVELOPMENT','wins':2,'panels':2},'characterization_verdict':verdict,'characterization_wins':sum(x['win'] for x in panels),'characterization_panels':4,'panels':panels,'pretruth_freeze_sha256':sha(a.freeze),'truth_access_before_pretruth':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False};s=dump(a.output/'RESULT.json',out);print(json.dumps({'verdict':verdict,'wins':sum(x['win'] for x in panels),'result_sha256':s,'panels':[{'pair':x['pair'],'year':x['year'],'physcore_f1':x['physcore']['macro_f1'],'literature_f1':x['literature']['macro_f1'],'physcore_recovered':x['physcore']['recovered_f1_gt_0_5'],'literature_recovered':x['literature']['recovered_f1_gt_0_5'],'win':x['win']} for x in panels]},indent=2))
if __name__=='__main__':main()
