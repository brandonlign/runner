#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from collections import Counter
from pathlib import Path
from typing import Any
EXPECTED_BASELINE_GZIP_SHA256='6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100'
EXPECTED_BASELINE_INNER_SHA256='7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53'
EXPECTED_ALL={2019:1,2020:4,2021:1,2022:10,2023:8,2024:14,2025:34,2026:29}; EXPECTED_CANONICAL={2022:10,2023:8,2024:14,2025:34,2026:29}; TARGET_TOTAL=18; MAX_RANK=100; MIN22=4; MIN23=4; MINTOTAL=8; F1MIN=0.5
def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s:str)->str:return re.sub(r'[^a-z0-9]','',str(s).lower())
def canonical(path:Path):
    with zipfile.ZipFile(path) as z:
        hits=[n for n in z.namelist() if Path(n).name=='april_candidate_members.csv']; req(len(hits)==1,f'canonical csv {hits}'); rows=list(csv.DictReader(io.StringIO(z.read(hits[0]).decode('utf-8-sig'))))
    req(rows,'empty canonical'); fields=list(rows[0]); by={norm(x):x for x in fields}; idcol=next((by[k] for k in ('eventid','event','trajectoryid','id','uniquetrajectoryidentifier') if k in by),None)
    if idcol is None:
        idcol=next((f for f in fields if 'id' in norm(f) and ('event' in norm(f) or 'trajectory' in norm(f))),None)
    req(idcol is not None,f'no id column {fields}'); yearcol=next((f for f in fields if norm(f) in ('year','yr')),None); parsed=[]
    for r in rows:
        eid=str(r[idcol]).strip(); req(eid,'empty id');
        if yearcol and str(r[yearcol]).strip(): y=int(float(r[yearcol]))
        else:
            m=re.search(r'20(19|20|21|22|23|24|25|26)',eid); req(m is not None,f'cannot year {eid}'); y=int(m.group(0))
        parsed.append((eid,y))
    req(len(set(x for x,_ in parsed))==len(parsed),'duplicate canonical'); counts=Counter(y for _,y in parsed); req(dict(sorted(counts.items()))==EXPECTED_ALL,f'historical counts {dict(counts)}'); can=[x for x in parsed if x[1] in EXPECTED_CANONICAL]; req(dict(sorted(Counter(y for _,y in can).items()))==EXPECTED_CANONICAL,'canonical counts'); return can,idcol,yearcol
def q(ids:set[str],t22:set[str],t23:set[str])->dict[str,Any]:
    a=sorted(ids&t22); b=sorted(ids&t23); n=len(a)+len(b); p=n/len(ids) if ids else 0.; r=n/TARGET_TOTAL; f=2*p*r/(p+r) if p+r else 0.; return {'overlap_2022_ids':a,'overlap_2023_ids':b,'overlap_2022':len(a),'overlap_2023':len(b),'overlap_total':n,'precision':p,'recall':r,'f1':f}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--stage-a',type=Path,required=True); ap.add_argument('--stage-a-sha256',type=Path,required=True); ap.add_argument('--canonical-zip',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True); recorded=a.stage_a_sha256.read_text().split()[0]; actual=sha(a.stage_a); req(recorded==actual,'stage-a digest mismatch'); pre=json.loads(a.stage_a.read_text()); req(pre['schema']=='ORBITTRACE_M2D_SACV_V1_FINAL_TARGET_PRETRUTH','schema'); req(pre['scientific_role']=='TOP100_ALREADY_BLIND_M2D_RANKING_WITH_FROZEN_SACV_MEMBERSHIPS_BEFORE_TARGET_REFERENCE_ACCESS','role'); req(pre['baseline_pretruth_gzip_sha256']==EXPECTED_BASELINE_GZIP_SHA256 and pre['baseline_pretruth_inner_sha256']==EXPECTED_BASELINE_INNER_SHA256,'baseline identity'); req(pre['frozen_candidate_count']==len(pre['extractions'])==MAX_RANK,'candidate count'); req([r['rank'] for r in pre['extractions']]==list(range(1,MAX_RANK+1)),'rank order')
    for k in ('target_reference_access','target_information_used','target_coordinates_accessed','canonical_target_ids_accessed','prior_target_reveal_artifact_accessed','target_aware_parent_selection','reranking_used','family_merge_used','post_result_parameter_search'): req(pre[k] is False,f'firewall {k}')
    can,idcol,yearcol=canonical(a.canonical_zip); t22={x for x,y in can if y==2022};t23={x for x,y in can if y==2023};req(len(t22)==10 and len(t23)==8,'target counts'); evaluated=[]
    for r in pre['extractions']:
        ids=set(map(str,r['output_ids'])); req(len(ids)==int(r['output_n']),'output size'); z=q(ids,t22,t23); support=z['overlap_2022']>=MIN22 and z['overlap_2023']>=MIN23 and z['overlap_total']>=MINTOTAL; clean=support and z['f1']>F1MIN; evaluated.append({'rank':int(r['rank']),'family_hash':str(r['family_hash']),'parent_member_count':int(r['parent_n']),'extraction_member_count':int(r['output_n']),'refined':bool(r['refined']),'extraction':z,'support_gate':support,'clean_f1_gate':z['f1']>F1MIN,'clean_success_gate':clean})
    partial=[x for x in evaluated if x['support_gate']]; clean=[x for x in evaluated if x['clean_success_gate']]; selected=(clean or partial or [None])[0]; verdict='CLEAN_M2D_SACV_V1_ORBITTRACE_REDISCOVERY' if clean else ('PARTIAL_M2D_SACV_V1_ORBITTRACE_RECOVERY' if partial else 'NO_M2D_SACV_V1_ORBITTRACE_RECOVERY')
    result={'verdict':verdict,'stage_a_sha256':actual,'baseline_pretruth_gzip_sha256':EXPECTED_BASELINE_GZIP_SHA256,'baseline_pretruth_inner_sha256':EXPECTED_BASELINE_INNER_SHA256,'frozen_candidate_count':MAX_RANK,'target_counts':{'2022':10,'2023':8,'total':18},'success_rule':{'maximum_original_parent_rank':MAX_RANK,'minimum_exact_2022_ids':MIN22,'minimum_exact_2023_ids':MIN23,'minimum_exact_total_ids':MINTOTAL,'exact_target_f1_strictly_greater_than':F1MIN},'first_original_rank_with_support_gate':partial[0]['rank'] if partial else None,'first_original_rank_with_clean_success_gate':clean[0]['rank'] if clean else None,'selected_candidate':selected,'evaluated':evaluated,'reveal_operation':'exact trajectory-ID set intersection only against already-frozen SACV memberships','coordinates_used':False,'activity_interval_used':False,'orbit_matching_used':False,'nearest_target_matching_used':False,'membership_recomputed_after_reveal':False,'parent_switched_after_reveal':False,'family_merge_used':False,'reranking_used':False,'parameter_tuning_after_reveal':False,'second_scientific_reveal_authorized':False,'canonical_column':idcol,'canonical_year_column':yearcol}
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print('BINDING_SACV_TARGET_VERDICT',verdict); print(json.dumps({'first_support_rank':result['first_original_rank_with_support_gate'],'first_clean_rank':result['first_original_rank_with_clean_success_gate'],'selected':selected},indent=2,sort_keys=True)); return 0
if __name__=='__main__':raise SystemExit(main())
