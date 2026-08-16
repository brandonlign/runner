#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

SOURCE_PRELABEL_SHA="db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de"
ORBIT_MAPPING_SHA="a99fdc71beb8ea78b957c0951191c66bf8c04e6ce04773952ac0c43695619f44"
STRUCTURAL_SHA="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--orbital-source',type=Path,required=True); ap.add_argument('--source-prelabel',type=Path,required=True); ap.add_argument('--orbit-mapping',type=Path,required=True); ap.add_argument('--availability-result',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.source_prelabel)==SOURCE_PRELABEL_SHA,'#1284 source prelabel hash changed'); src=json.loads(a.source_prelabel.read_text())
    req(src['schema']=='ORBITTRACE_TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL' and src['scientific_role']=='PRELABEL_TOPOMODAL_SPARSE_RECOVERY_V1','#1284 prelabel schema'); req(src['shower_truth_used'] is False and src['target_information_access'] is False and src['target_region_events_accessed'] is False,'source prelabel firewall'); req(src['structural_result_sha256']==STRUCTURAL_SHA and len(src['subsets'])==8,'source structural pin')
    req(sha(a.orbit_mapping)==ORBIT_MAPPING_SHA,'orbit mapping hash changed'); mapping=json.loads(a.orbit_mapping.read_text()); req(len(mapping)==23080 and all(v is not None for v in mapping.values()),'orbit mapping incomplete')
    avail=json.loads(a.availability_result.read_text()); req(avail['verdict']=='PASS_TOPOMODAL_ORBIT_AVAILABILITY_V1' and avail['orbit_mapping_sha256']==ORBIT_MAPPING_SHA,'orbit availability prerequisite'); req(all(v['all_events_usable'] for v in avail['subset_stats'].values()),'incomplete orbit panel')
    orbital=load(a.orbital_source,'orbf_frozen_math')
    out_sub=[]
    for row in src['subsets']:
        d,b=int(row['denominator']),int(row['bucket']); original=list(row['topomodal_candidates']); recurrent=list(row['recurrent_candidates']); req(len(original)==int(row['topomodal_summary']['candidate_count']) and len(recurrent)==int(row['recurrent_summary']['candidate_count']),'source candidate count'); req(len(original)>=len(recurrent)>0,'equal-budget shortage')
        ranked=orbital.orbital_order(original,mapping); req(len(ranked)==len(original),'rerank candidate count changed'); req(sorted((r['family_hash'],tuple(r['event_ids'])) for r in ranked)==sorted((r['family_hash'],tuple(r['event_ids'])) for r in original),'rerank membership changed')
        out_sub.append({'denominator':d,'bucket':b,'events_total':int(row['events_total']),'events_by_year':row['events_by_year'],'event_universe_sha256':str(row['event_universe_sha256']),'equal_budget_k':len(recurrent),'candidate_budget_sufficient':True,'successor_summary':row['topomodal_summary'],'recurrent_summary':row['recurrent_summary'],'successor_candidates':ranked,'recurrent_candidates':recurrent})
    pre={'schema':'ORBITTRACE_TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL','scientific_role':'PRELABEL_TOPOMODAL_ORBITAL_FRECHET_V1','years':[2022,2023],'blind_exclusion':[20.0,55.0],'source_1284_prelabel_sha256':SOURCE_PRELABEL_SHA,'structural_result_sha256':STRUCTURAL_SHA,'orbit_mapping_sha256':ORBIT_MAPPING_SHA,'intrinsic_source_blob':INTRINSIC_BLOB,'configuration':{'candidate_generator':'exact_1284_complete_topomodal_hierarchy','density':'exact_1284_radius_degree_over_subset_n','graph':'exact_1284_physical_radius_1','min_candidate_support':4,'orbital_dissimilarity':'Southworth_Hawkins_D_SH_squared_exact_appendix_formula','orbital_center':'observed_member_Frechet_medoid','orbital_energy':'minimum_mean_D_SH_squared_to_all_other_candidate_members','ranking':'roots_first_then_orbital_frechet_energy_ascending_then_family_hash','equal_budget':'recurrent_candidate_count'},'subsets':out_sub,'candidate_budget_shortage_any_panel':False,'shower_truth_used':False,'shower_truth_parsed':False,'iau_number_parsed':False,'iau_code_parsed':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    p=a.output/'TOPOMODAL_ORBITAL_FRECHET_V1_PRELABEL.json'; p.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'prelabel_sha256':sha(p),'source_1284_prelabel_sha256':SOURCE_PRELABEL_SHA,'orbit_mapping_sha256':ORBIT_MAPPING_SHA,'candidate_counts':[{'d':r['denominator'],'b':r['bucket'],'successor':len(r['successor_candidates']),'parent':len(r['recurrent_candidates'])} for r in out_sub]},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
