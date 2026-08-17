#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
PAIRS=('sugar','dsh'); YEARS=(2013,2014)
def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path)->Any:return json.loads(p.read_text())
def dump(p:Path,o:Any)->str:
    raw=(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();p.write_bytes(raw);return hashlib.sha256(raw).hexdigest()
def scientific_families(d):
    return [(int(f['rank']),str(f['parent_family_id']),tuple(str(x) for x in f['event_ids']),bool(f['fallback_to_parent'])) for f in d['families']]
def main():
    p=argparse.ArgumentParser(); p.add_argument('--rows',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--direct',type=Path,required=True);p.add_argument('--comparators',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    eq=[]
    for y in YEARS:
        transfer=load(a.generated/f'physcore_hdbscan_{y}'/f'physcore_hdbscan_{y}.json'); direct=load(a.direct/'pretruth'/f'physcore_{y}.json')
        req(scientific_families(transfer)==scientific_families(direct),f'transfer not exactly equivalent in {y}')
        eq.append({'year':y,'exact_membership_equivalence':True,'transfer_family_count':transfer['family_count'],'direct_family_count':direct['family_count'],'direct_candidate_sha256':sha(a.direct/'pretruth'/f'physcore_{y}.json'),'transfer_candidate_sha256':sha(a.generated/f'physcore_hdbscan_{y}'/f'physcore_hdbscan_{y}.json')})
    panels=[]
    for pair in PAIRS:
        for y in YEARS:
            cp=a.generated/f'physcore_{pair}_{y}'/f'physcore_{pair}_{y}.json'; cm=a.generated/f'physcore_{pair}_{y}'/f'physcore_{pair}_{y}_manifest.json'; hp=a.generated/f'parent_{pair}_{y}'/'comparator_primary_output.json'; hm=a.generated/f'parent_{pair}_{y}'/'comparator_source_manifest.json'; rp=a.rows/f'{pair}_{y}.json'; lp=a.comparators/f'{pair}_{y}'/'comparator_primary_output.json'; lm=a.comparators/f'{pair}_{y}'/'comparator_source_manifest.json'
            c=load(cp); h=load(hp); l=load(lp); req(c['truth_accessed'] is False and h['truth_accessed'] is False,'truth in generated pretruth');req(c['family_count']==h['retained_family_count'],'physcore parent count mismatch');req(int(l['retained_family_count'])>0,'empty literature comparator')
            ids=sorted(str(x['id']) for x in load(rp)); ids_sha=hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest()
            panels.append({'pair':pair,'year':y,'pairwise_rows_json_sha256':sha(rp),'pairwise_event_ids_sha256':ids_sha,'physcore_output_sha256':sha(cp),'physcore_manifest_sha256':sha(cm),'parent_hdbscan_output_sha256':sha(hp),'parent_hdbscan_manifest_sha256':sha(hm),'literature_output_sha256':sha(lp),'literature_manifest_sha256':sha(lm),'physcore_family_count':c['family_count'],'literature_family_count':l['retained_family_count']})
    out={'schema':'ORBITTRACE_PHYSCORE_MATCHED_LITERATURE_V1_PRETRUTH_FREEZE','pretruth_outputs_frozen':True,'truth_accessed_before_freeze':False,'transfer_equivalence':eq,'panels':panels,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False};s=dump(a.output/'PRETRUTH_FREEZE.json',out);print(json.dumps({'pretruth_freeze_sha256':s,'panels':len(panels),'transfer_equivalence':True},indent=2))
if __name__=='__main__':main()
