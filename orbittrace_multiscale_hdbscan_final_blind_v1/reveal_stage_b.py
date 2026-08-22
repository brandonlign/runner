#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,zipfile
from collections import Counter
from pathlib import Path

EXPECTED_ALL={2019:1,2020:4,2021:1,2022:10,2023:8,2024:14,2025:34,2026:29}
EXPECTED_CANONICAL={2022:10,2023:8,2024:14,2025:34,2026:29}
GRID=[10,20,30,40,50,60,70,80,90,100,120,150,200,300,500,750,1000]
WEIGHTS=[0.335,0.25,0.23,0.215,0.128,0.145,1.0,0.0]
TARGET_TOTAL=18; MAX_RANK=100; MIN22=4; MIN23=4; MINTOTAL=8; F1MIN=0.5

def req(x,msg):
    if not x: raise RuntimeError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r'[^a-z0-9]','',str(s).lower())

def canonical(path:Path):
    with zipfile.ZipFile(path) as z:
        hits=[n for n in z.namelist() if Path(n).name=='april_candidate_members.csv']
        req(len(hits)==1,f'canonical csv {hits}')
        rows=list(csv.DictReader(io.StringIO(z.read(hits[0]).decode('utf-8-sig'))))
    req(rows,'empty canonical')
    fields=list(rows[0]); by={norm(x):x for x in fields}
    idcol=next((by[k] for k in ('eventid','event','trajectoryid','id','uniquetrajectoryidentifier') if k in by),None)
    if idcol is None:idcol=next((f for f in fields if 'id' in norm(f) and ('event' in norm(f) or 'trajectory' in norm(f))),None)
    req(idcol is not None,f'no id column {fields}')
    yearcol=next((f for f in fields if norm(f) in ('year','yr')),None)
    parsed=[]
    for r in rows:
        eid=str(r[idcol]).strip();req(eid,'empty canonical id')
        if yearcol and str(r[yearcol]).strip():y=int(float(r[yearcol]))
        else:
            m=re.search(r'20(19|20|21|22|23|24|25|26)',eid);req(m is not None,f'cannot infer year {eid}');y=int(m.group(0))
        parsed.append((eid,y))
    req(len(set(x for x,_ in parsed))==len(parsed),'duplicate canonical')
    counts=Counter(y for _,y in parsed);req(dict(sorted(counts.items()))==EXPECTED_ALL,f'canonical historical counts {dict(counts)}')
    can=[x for x in parsed if x[1] in EXPECTED_CANONICAL]
    req(dict(sorted(Counter(y for _,y in can).items()))==EXPECTED_CANONICAL,'canonical target counts')
    return can,idcol,yearcol

def quality(ids,t22,t23):
    a=sorted(ids&t22);b=sorted(ids&t23);n=len(a)+len(b);p=n/len(ids) if ids else 0.0;r=n/TARGET_TOTAL;f=2*p*r/(p+r) if p+r else 0.0
    return {'overlap_2022_ids':a,'overlap_2023_ids':b,'overlap_2022':len(a),'overlap_2023':len(b),'overlap_total':n,'precision':p,'recall':r,'f1':f}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage-a',type=Path,required=True);ap.add_argument('--stage-a-sha256',type=Path,required=True);ap.add_argument('--canonical-zip',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    recorded=a.stage_a_sha256.read_text().split()[0];actual=sha(a.stage_a);req(recorded==actual,'stage-a digest mismatch')
    pre=json.loads(a.stage_a.read_text());req(pre['schema']=='ORBITTRACE_MULTISCALE_HDBSCAN_FINAL_BLIND_V1_STAGE_A','stage-a schema');req(pre['scientific_role']=='TARGET_INCLUSIVE_GMN_2022_2023_LABEL_FREE_MULTISCALE_RANKING','stage-a role');req(pre['event_count']==549636,'event count drift');req(pre['grid']==GRID,'grid drift');req(pre['weights']==WEIGHTS,'weight drift');req(abs(float(pre['lambda'])-0.25)<1e-15,'lambda drift');req(pre['auxiliary_recurrent_hdbscan']=={'min_cluster_size':10,'min_samples':10,'reportable':False,'candidate_count':pre['auxiliary_recurrent_hdbscan']['candidate_count']},'auxiliary recurrent identity drift')
    req(len(pre['top100'])==MAX_RANK and [int(x['rank']) for x in pre['top100']]==list(range(1,MAX_RANK+1)),'top100 rank drift')
    for k in ('target_reference_access','canonical_target_ids_accessed','target_coordinates_accessed','activity_interval_used','shower_labels_used','post_result_parameter_search','reranking_after_reveal'):req(pre[k] is False,f'firewall {k}')
    can,idcol,yearcol=canonical(a.canonical_zip);t22={x for x,y in can if y==2022};t23={x for x,y in can if y==2023};req(len(t22)==10 and len(t23)==8,'target year counts')
    evaluated=[]
    for row in pre['top100']:
        ids=set(map(str,row['event_ids']));req(len(ids)==int(row['member_count']),'candidate member count drift');z=quality(ids,t22,t23);support=z['overlap_2022']>=MIN22 and z['overlap_2023']>=MIN23 and z['overlap_total']>=MINTOTAL;clean=support and z['f1']>F1MIN;evaluated.append({'rank':int(row['rank']),'family_hash':str(row['family_hash']),'member_count':int(row['member_count']),'scales':row['scales'],'quality':z,'support_gate':support,'clean_f1_gate':z['f1']>F1MIN,'clean_success_gate':clean})
    partial=[x for x in evaluated if x['support_gate']];clean=[x for x in evaluated if x['clean_success_gate']];selected=(clean or partial or [None])[0]
    verdict='CLEAN_MULTISCALE_HDBSCAN_ORBITTRACE_DISCOVERY' if clean else ('PARTIAL_MULTISCALE_HDBSCAN_ORBITTRACE_RECOVERY' if partial else 'NO_MULTISCALE_HDBSCAN_ORBITTRACE_RECOVERY')
    out={'verdict':verdict,'stage_a_sha256':actual,'frozen_candidate_count':MAX_RANK,'target_counts':{'2022':10,'2023':8,'total':18},'success_rule':{'maximum_rank':MAX_RANK,'minimum_exact_2022_ids':MIN22,'minimum_exact_2023_ids':MIN23,'minimum_exact_total_ids':MINTOTAL,'exact_target_f1_strictly_greater_than':F1MIN},'first_rank_with_support_gate':partial[0]['rank'] if partial else None,'first_rank_with_clean_success_gate':clean[0]['rank'] if clean else None,'selected_candidate':selected,'evaluated':evaluated,'reveal_operation':'exact trajectory-ID set intersection only against already-frozen multiscale memberships','membership_recomputed_after_reveal':False,'reranking_after_reveal':False,'family_merge_after_reveal':False,'target_distance_matching_used':False,'parameter_tuning_after_reveal':False,'second_scientific_reveal_authorized':False,'canonical_column':idcol,'canonical_year_column':yearcol}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print('BINDING_MULTISCALE_TARGET_VERDICT',verdict);print(json.dumps({'first_support_rank':out['first_rank_with_support_gate'],'first_clean_rank':out['first_rank_with_clean_success_gate'],'selected':selected},indent=2,sort_keys=True))
if __name__=='__main__':main()
