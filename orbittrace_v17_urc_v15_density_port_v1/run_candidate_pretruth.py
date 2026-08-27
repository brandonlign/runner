#!/usr/bin/env python3
from __future__ import annotations

import argparse, copy, hashlib, importlib.util, json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_pooled_year_centroid_v8 import run_development as v8
from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v16_v15_joint_conformal_membership_v1 import expand_candidate as jc
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS=(2013,2014)
MULT=v6.mult
EXPAND_TOP_K=100
EXPECTED_MODEL_SHA='ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED_RANKER_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'


def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dump(path: Path,obj: Any)->str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n').encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot load {path}')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def build_hard_with_v15_order(*,scan_by_year,support,base,runtime):
    components=[]; components_by_year={}; passing_by_year={}; audits=[]
    for year in YEARS:
        audit,passing,year_components=v6.label_free_scan_year(year,scan_by_year[year],support,base)
        require(audit['calibration_events_used']==0,'label calibration reached v17')
        require(audit['source_labels_used_for_proposals'] is False,'labels reached v17 proposals')
        passing_by_year[year]=passing; components_by_year[year]=year_components; components.extend(year_components); audits.append(audit)
    families,rankings=support.build_families(components,base)
    require(families,'no hard recurrent families')
    require(set(map(str,rankings['persistence']))=={str(f['family_id']) for f in families},'hard family universe incomplete')
    repair=v8.repair_year_centroids(families,components,scan_by_year,support,base)
    require(repair['non_centroid_family_structure_unchanged'] is True,'centroid repair changed hard structure')
    component_orders={}; component_summaries={}
    for cap in v15_application.COMPONENT_CAPS:
        _scored,order,summary=v15_application.score_component(
            families=families,scan_by_year=scan_by_year,years=YEARS,cap=cap,runtime=runtime,base=base,score_episode=MULT.score_episode)
        component_orders[cap]=order; component_summaries[str(cap)]=summary
    hard_order,rows=v15_application.consensus_order(component_orders)
    require(set(hard_order)=={str(f['family_id']) for f in families},'v15 hard order incomplete')
    return {
        'hard_families':families,'hard_order':hard_order,'components':components,
        'components_by_year':components_by_year,'passing_by_year':passing_by_year,
        'scan_audits':audits,'repair':repair,'v15_rows':rows,'v15_component_summaries':component_summaries,
    }


def expand_top_ranked_memberships(*,families,scan_by_year):
    expanded=copy.deepcopy(families)
    lookup={y:{str(e['id']):e for e in scan_by_year[y]} for y in YEARS}
    original={str(f['family_id']):set(map(str,f['event_ids'])) for f in expanded}
    rank_by_id={str(f['family_id']):int(f['rank']) for f in expanded}
    top_ids={str(f['family_id']) for f in expanded if int(f['rank'])<=EXPAND_TOP_K}
    by_id={str(f['family_id']):f for f in expanded}
    diagnostics={'expand_top_k':EXPAND_TOP_K,'fixed_membership_source':'pre-SonotaCo PR #461','eligible_family_year_pairs':0,'ineligible_family_year_pairs':0,'new_members_by_year':{},'eligible_pairs_by_year':{},'conflicted_additions_by_year':{}}
    for target_year in YEARS:
        source_year=YEARS[1] if target_year==YEARS[0] else YEARS[0]
        target=scan_by_year[target_year]; target_sol=np.asarray([float(e['sol'])%360.0 for e in target],dtype=np.float64)
        best={}; eligible_pairs=0
        for fid in sorted(top_ids,key=lambda x:(rank_by_id[x],x)):
            source_ids=sorted(original[fid] & set(lookup[source_year]))
            if len(source_ids)<4:
                diagnostics['ineligible_family_year_pairs']+=1; continue
            diagnostics['eligible_family_year_pairs']+=1
            source=[lookup[source_year][eid] for eid in source_ids]
            sd2=jc.source_leave_one_out_d2(source); sr=jc.loo_residuals(source)
            source_scores=jc.fisher_nonconformity(jc.source_empirical_pvalues(sd2),jc.source_empirical_pvalues(sr)); model=jc.fit_trajectory(source)
            idx=np.flatnonzero(jc.in_activity_arc(target_sol,[float(e['sol']) for e in source]))
            candidates=[target[int(i)] for i in idx]
            d2=jc.target_d2(candidates,source); residual=jc.trajectory_residuals(model,candidates)
            scores=jc.fisher_nonconformity(jc.target_empirical_pvalues(d2,sd2),jc.target_empirical_pvalues(residual,sr)); jp=jc.joint_conformal_pvalues(scores,source_scores)
            for i,d,r,s,p in zip(idx.tolist(),d2.tolist(),residual.tolist(),scores.tolist(),jp.tolist()):
                eid=str(target[i]['id'])
                if eid in original[fid]: continue
                if float(d)>jc.DENSITY_CEILING+1e-12 or float(r)>jc.TRAJECTORY_CEILING+1e-12 or float(p)<=jc.ALPHA+1e-15: continue
                eligible_pairs+=1
                key=(-float(p),float(s),rank_by_id[fid],fid)
                old=best.get(eid)
                if old is None or key<old[0]: best[eid]=(key,fid)
        additions=defaultdict(list)
        for eid,(_key,fid) in best.items(): additions[fid].append(eid)
        for fid,ids in additions.items():
            by_id[fid]['event_ids']=sorted(set(map(str,by_id[fid]['event_ids']))|set(ids))
        diagnostics['new_members_by_year'][str(target_year)]=len(best)
        diagnostics['eligible_pairs_by_year'][str(target_year)]=eligible_pairs
        diagnostics['conflicted_additions_by_year'][str(target_year)]=max(0,eligible_pairs-len(best))
    diagnostics['total_new_members']=sum(diagnostics['new_members_by_year'].values())
    diagnostics['expanded_membership_sha256']=canonical_sha({str(f['family_id']):sorted(map(str,f['event_ids'])) for f in expanded if int(f['rank'])<=EXPAND_TOP_K})
    for before,after in zip(families,expanded):
        require(str(before['family_id'])==str(after['family_id']) and int(before['rank'])==int(after['rank']),'rank/order changed during membership')
        require(set(map(str,before['event_ids'])).issubset(set(map(str,after['event_ids']))),'original seed removed')
    return expanded,diagnostics


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--comparator',choices=['sugar','hdbscan'],required=True)
    p.add_argument('--rows-2013',type=Path,required=True); p.add_argument('--rows-2014',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True); p.add_argument('--candidate-payload',type=Path,required=True); p.add_argument('--baseline-payload',type=Path,required=True); p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--active-ranker-source',type=Path,required=True); p.add_argument('--model-joblib',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.active_ranker_source)==EXPECTED_RANKER_SHA,'#839 scientific ranker source changed'); require(sha(a.model_joblib)==EXPECTED_MODEL_SHA,'#853 serialized model changed')
    raw={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    for year in YEARS:
        require(raw[year] and all(int(x['year'])==year for x in raw[year]),f'invalid {year} rows')
        forbidden={'label','shower','truth','known_shower','native_background','sporadic'}
        require(all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),'truth-bearing field reached v17 input')
    canonical=v15_application.validate_pair(YEARS,raw)
    runtime,support,base,_=load_support_base(p19_module=type('Shim',(),{'mult':MULT})(),support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
    generators.configure_pair(YEARS,support=support,mult=MULT,v6=v6,v8=v8,p19=p19,p20=p20)
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'target firewall changed')
    support.CORPUS=p19.CORPUS
    hard=build_hard_with_v15_order(scan_by_year=canonical,support=support,base=base,runtime=runtime)
    p19_soft,p19_diag=generators.build_p19_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p19=p19)
    p20_result=generators.build_p20_pair(years=YEARS,hard=hard,scan_by_year=canonical,support=support,base=base,p20=p20)
    p20_soft=p20_result['soft_families']; union=hard['hard_families']+p19_soft+p20_soft
    source_by_id={str(f['family_id']):'hard' for f in hard['hard_families']}; source_by_id.update({str(f['family_id']):'p19' for f in p19_soft}); source_by_id.update({str(f['family_id']):'p20' for f in p20_soft})
    require(len(source_by_id)==len(union),'union family IDs collide')
    urc=load_module(a.active_ranker_source,'frozen_active_urc_v17')
    rank=urc_application.score_and_rank(model_path=a.model_joblib,families=union,source_by_id=source_by_id,hard_order=hard['hard_order'],scan_by_year=canonical,years=YEARS,support=support,base=base,frozen_ranker_module=urc)
    by_id={str(f['family_id']):f for f in union}; ordered=[]
    for i,fid in enumerate(rank['order'],start=1):
        f=by_id[fid]; ordered.append({'family_id':fid,'rank':i,'event_ids':sorted(set(map(str,f['event_ids']))),'source':source_by_id[fid]})
    expanded,membership_diag=expand_top_ranked_memberships(families=ordered,scan_by_year=canonical)
    primary={
        'method':'OrbitTrace v17 broad URC + v15 density-stable hard rank + frozen #839 quality/diversity + frozen joint-conformal top100 membership',
        'comparator_pair':a.comparator,'years':list(YEARS),'family_count':len(expanded),'families':expanded,
        'candidate_counts':{'hard':len(hard['hard_families']),'p19':len(p19_soft),'p20':len(p20_soft),'union':len(union)},
        'hard_order_method':'v15 median-rank consensus over adaptive caps 128/96/64','hard_order_sha256':canonical_sha(hard['hard_order']),
        'urc_application_order_sha256':rank['order_sha256'],'ranker_model_sha256':EXPECTED_MODEL_SHA,'ranker_source_sha256':EXPECTED_RANKER_SHA,
        'membership_diagnostics':membership_diag,'p19_diagnostics':p19_diag,'p20_diagnostics':p20_result['soft_diagnostics'],
        'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    primary_sha=dump(a.output/'candidate_primary_output.json',primary)
    summary={'verdict':'PASS_V17_EXPOSED_DEVELOPMENT_PRETRUTH_OUTPUT_FREEZE','comparator':a.comparator,'primary_output_sha256':primary_sha,'family_count':len(expanded),'candidate_counts':primary['candidate_counts'],'membership_total_new':membership_diag['total_new_members'],'truth_accessed':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    dump(a.output/'candidate_pretruth_summary.json',summary); print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
