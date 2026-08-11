#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from typing import Any
from orbittrace_v45_component_prioritized_joint_slot_v1 import train_evaluate as v45
v40=v45.v40
VARIANT='inheritance_gap_joint_slot_permutation_v1'
PROTOCOL_BLOB='e16ad5c66280794a37802b2640d783c174448e32'
SIGNAL_SHA='a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
AUTH_RUN=31488131546; AUTH_ART=9099927842
AUTH_DIGEST='sha256:67960fbd5fd76173da62c6d1823d507c99ee6431862ce56351aa7a194ec81e07'
AUTH_RESULT_SHA='c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461'
AUTH_VECTOR_SHA='145ceb528e66f924c00c152cf2e5a38a2424ffda8f0a39a7eb80680c1bd5dadd'
AUTH_VECTOR_CANON='0a9eda015ca367697a1dca678a0e8f7d986880fc424a0cbf4573567ab8776672'
HDB_N=229; SUGAR_N=267; JOINT_N=60
_ORIG_BUILD=v45.build_v45_order
_V47_ORDER:list[str]=[]; _V31_ORDER:list[str]=[]; _GAP:dict[str,float]={}; _AUTH_VECTOR:Path|None=None

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def osha(xs:list[str])->str:return hashlib.sha256('\n'.join(map(str,xs)).encode()).hexdigest()
def canon(d:dict[str,Any])->str:
    x=dict(d);x.pop('canonical_sha256_without_self_field',None)
    return hashlib.sha256((json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).hexdigest()

def auth(result:Path,vector:Path)->tuple[dict[str,Any],dict[str,Any]]:
    req(sha(result)==AUTH_RESULT_SHA,'#1139 result identity changed');req(sha(vector)==AUTH_VECTOR_SHA,'#1139 vector identity changed')
    r=json.loads(result.read_text());v=json.loads(vector.read_text())
    req(r['verdict']=='PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC' and r['scientific_role']=='POST_V46_DIAGNOSTIC_ONLY_JOINT_INHERITANCE_GAP_NO_SUCCESSOR_EVALUATED','#1139 result changed')
    req(r['source_1098_run']==31457923695 and r['source_1098_artifact']==9088724826 and r['source_signal_sha256']==SIGNAL_SHA,'#1139 provenance changed')
    req(r['joint_family_count']==JOINT_N and r['direction_supported_both_years'] is True and set(r['annual_diagnostics'])=={'2013','2014'},'#1139 direction changed')
    for y in ('2013','2014'):
        a=r['annual_diagnostics'][y];req(a['direction_pass'] is True and a['recoverable']['median_inheritance_gap']<a['nonrecoverable']['median_inheritance_gap'],f'#1139 {y} direction changed')
    for k in ('new_rank_or_score_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','group_aggregation_evaluated','auc_evaluated','correlation_evaluated','regression_evaluated','p_value_evaluated','threshold_search','quantile_search','top_k_search','rank_window_search','alternate_statistic_search','alternate_direction_test','component_size_rule_search','quality_rank_placement_retry','component_placement_retry','component_representative_retry','pareto_layer_evaluated','pairwise_dominance_evaluated','boundary_identity_used','boundary_rescue_list_created','oracle_identity_used_for_ranking','truth_aware_group_identity_used_for_ranking','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        req(r[k] is False,f'#1139 forbidden result flag {k}')
    req(r['sonotaco_role']=='EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion']==[20.0,55.0],'#1139 firewall changed')
    req(v['verdict']=='PASS_V46_JOINT_INHERITANCE_GAP_VECTOR_FREEZE' and v['scientific_role']=='EXACT_60_JOINT_FAMILY_INHERITANCE_GAP_FROZEN_BEFORE_OUTCOME_TRUTH','#1139 vector changed')
    req(v['source_signal_sha256']==SIGNAL_SHA and v['family_count']==HDB_N and v['joint_family_count']==JOINT_N and len(v['families'])==JOINT_N,'#1139 vector provenance/count changed')
    req(v['canonical_sha256_without_self_field']==AUTH_VECTOR_CANON and canon(v)==AUTH_VECTOR_CANON,'#1139 vector canonical identity changed')
    req(v['truth_accessed'] is False and v['literature_budget_used'] is False and v['boundary_identity_used'] is False,'#1139 vector truth/budget dependence')
    for k in ('new_rank_or_score_evaluated','selector_evaluated','successor_selected','threshold_selected','top_k_selected','rank_window_selected','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
        req(v[k] is False,f'#1139 forbidden vector flag {k}')
    req(v['blind_exclusion']==[20.0,55.0],'#1139 vector firewall changed')
    return r,v

def signal(path:Path)->dict[str,Any]:
    req(sha(path)==SIGNAL_SHA,'#1098 signal identity changed');s=json.loads(path.read_text())
    req(s['verdict']=='PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE' and s['scientific_role']=='FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION','#1098 signal changed')
    req(s['family_count']==HDB_N and len(s['families'])==HDB_N and sum(bool(x['joint_signal']) for x in s['families'])==JOINT_N,'#1098 counts changed')
    req(s['graph_sha256']==v40.GRAPH_SHA256 and s['component_sha256']==v40.COMPONENT_SHA256,'#1098 geometry changed')
    req(s['target_information_access'] is False and s['target_region_events_accessed'] is False and s['maarsy_scientific_access'] is False and s['dms_scientific_access'] is False and s['blind_exclusion']==[20.0,55.0],'#1098 firewall changed')
    return s

def derive_order(s:dict[str,Any],v:dict[str,Any])->tuple[list[str],list[str],list[int],dict[str,float]]:
    by={str(x['family_id']):x for x in s['families']};req(len(by)==HDB_N,'duplicate #1098 identity')
    base=[str(x['family_id']) for x in sorted(s['families'],key=lambda x:(int(x['v31_rank']),str(x['family_id'])))]
    req([int(by[f]['v31_rank']) for f in base]==list(range(1,HDB_N+1)),'v31 ranks not permutation')
    vr={str(x['family_id']):x for x in v['families']};req(len(vr)==JOINT_N,'duplicate #1139 identity')
    joint=[f for f in base if bool(by[f]['joint_signal'])];req(set(joint)==set(vr),'#1098/#1139 joint identity mismatch')
    gap={}
    for f in joint:
        a=by[f];b=vr[f];g=float(b['inheritance_gap']);calc=float(b['v31_percentile'])-float(b['component_best_v31_percentile'])
        req(int(a['v31_rank'])==int(b['v31_rank']) and abs(float(a['v31_percentile'])-float(b['v31_percentile']))<1e-15 and abs(float(a['component_best_v31_percentile'])-float(b['component_best_v31_percentile']))<1e-15,'#1098/#1139 value mismatch')
        req(abs(g-calc)<1e-15 and g>0,'inheritance gap changed');gap[f]=g
    slots=sorted(int(by[f]['v31_rank']) for f in joint);ordered=sorted(joint,key=lambda f:(gap[f],int(by[f]['v31_rank']),f));out=list(base)
    for pos,f in zip(slots,ordered):out[pos-1]=f
    req(len(out)==HDB_N and len(set(out))==HDB_N and set(out)==set(base),'invalid v47 permutation')
    js=set(joint)
    for pos,f in enumerate(base,1):
        if pos not in slots:req(out[pos-1]==f and f not in js,f'nonjoint slot changed {pos}')
        else:req(out[pos-1] in js,f'nonjoint entered joint slot {pos}')
    return base,out,slots,gap

def pretruth_mode(sugar:Path,hdb:Path,out:Path)->int:return v45.pretruth_mode(sugar,hdb,out)

def freeze_order_mode(sig:Path,diag:Path,vec:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True);s=signal(sig);_,v=auth(diag,vec);base,order,slots,gap=derive_order(s,v)
    payload={'verdict':'PASS_V47_INHERITANCE_GAP_JOINT_SLOT_ORDER_FREEZE','scientific_role':'COMPLETE_V47_HDB_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_TRUTH','source_1098_run':31457923695,'source_1098_artifact':9088724826,'source_signal_sha256':SIGNAL_SHA,'authorizing_1139_run':AUTH_RUN,'authorizing_1139_artifact':AUTH_ART,'authorizing_1139_digest':AUTH_DIGEST,'authorizing_result_sha256':AUTH_RESULT_SHA,'authorizing_vector_sha256':AUTH_VECTOR_SHA,'authorizing_vector_canonical_sha256':AUTH_VECTOR_CANON,'family_count':HDB_N,'joint_family_count':JOINT_N,'nonjoint_family_count':HDB_N-JOINT_N,'priority':'(inheritance_gap, exact_v31_rank, family_id); lower first','slot_rule':'permute exact 60 joint-positive identities only across their exact-v31 occupied positions','v31_order':base,'v31_order_sha256':osha(base),'joint_positions':slots,'joint_family_ids':sorted(gap),'v47_order':order,'v47_order_sha256':osha(order),'truth_accessed':False,'literature_budget_used':False,'boundary_identity_used':False,'inheritance_gap_threshold_selected':False,'top_k_selected':False,'rank_window_selected':False,'pairwise_dominance_used':False,'successor_search_performed':False,'target_information_access':False,'target_region_events_accessed':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'blind_exclusion':[20.0,55.0]}
    payload['canonical_sha256_without_self_field']=canon(payload);p=out/'V47_INHERITANCE_GAP_JOINT_SLOT_ORDER_FREEZE.json';p.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':payload['verdict'],'v31_order_sha256':payload['v31_order_sha256'],'v47_order_sha256':payload['v47_order_sha256'],'canonical_sha256_without_self_field':payload['canonical_sha256_without_self_field'],'file_sha256':sha(p)},indent=2,sort_keys=True));return 0

def build_v47_order(route:str,base_order:list[str],components:list[dict[str,Any]],rank_maps:dict[str,dict[str,int]]):
    order,rows=_ORIG_BUILD(route,base_order,components,rank_maps)
    if route=='sugar':return order,rows
    req(list(map(str,base_order))==_V31_ORDER,'v47 evaluator v31 order differs from pretruth freeze')
    by={str(r['family_id']):r for r in rows};joint=[f for f in _V31_ORDER if bool(by[f]['joint_gate'])];req(set(joint)==set(_GAP) and len(joint)==JOINT_N,'v47 evaluator joint set changed')
    nr={f:i+1 for i,f in enumerate(_V47_ORDER)};slots=sorted(int(by[f]['v31_rank']) for f in joint);req(sorted(nr[f] for f in joint)==slots,'v47 joint slot set changed')
    for r in rows:
        f=str(r['family_id']);r['inheritance_gap']=_GAP.get(f);r['v45_rank']=nr[f];r['v45_rank_delta']=int(r['v31_rank'])-nr[f];r['v45_joint_slot_position']=nr[f] if bool(r['joint_gate']) else None
        if not bool(r['joint_gate']):req(nr[f]==int(r['v31_rank']),f'nonjoint moved {f}')
    return list(_V47_ORDER),rows

def auth_shim(path:Path)->None:
    req(_AUTH_VECTOR is not None,'v47 auth vector not initialized');auth(path,_AUTH_VECTOR)

def evaluate_mode(sugar:Path,hdb:Path,truth:Path,ranker:Path,graph:Path,components:Path,diag:Path,vec:Path,order_file:Path,out:Path)->int:
    out.mkdir(parents=True,exist_ok=True);_,v=auth(diag,vec);f=json.loads(order_file.read_text())
    req(f['verdict']=='PASS_V47_INHERITANCE_GAP_JOINT_SLOT_ORDER_FREEZE' and f['scientific_role']=='COMPLETE_V47_HDB_ORDER_FROZEN_BEFORE_CURRENT_OUTCOME_TRUTH','v47 order freeze changed')
    req(f['authorizing_result_sha256']==AUTH_RESULT_SHA and f['authorizing_vector_sha256']==AUTH_VECTOR_SHA and f['truth_accessed'] is False and f['literature_budget_used'] is False and f['boundary_identity_used'] is False,'v47 order freeze provenance changed')
    req(osha(list(map(str,f['v31_order'])))==f['v31_order_sha256'] and osha(list(map(str,f['v47_order'])))==f['v47_order_sha256'],'v47 order hash changed')
    global _V47_ORDER,_V31_ORDER,_GAP,_AUTH_VECTOR
    _V31_ORDER=list(map(str,f['v31_order']));_V47_ORDER=list(map(str,f['v47_order']));_GAP={str(x['family_id']):float(x['inheritance_gap']) for x in v['families']};_AUTH_VECTOR=vec
    req(len(_GAP)==JOINT_N,'v47 gap map changed')
    adapter=out/'_adapter';ob=v45.build_v45_order;ov=v45.VARIANT;oa=v45.validate_placement_diagnostic
    v45.build_v45_order=build_v47_order;v45.VARIANT=VARIANT;v45.validate_placement_diagnostic=auth_shim
    try:rc=v45.evaluate_mode(sugar,hdb,truth,ranker,graph,components,diag,adapter)
    finally:v45.build_v45_order=ob;v45.VARIANT=ov;v45.validate_placement_diagnostic=oa
    req(rc==0,'frozen v45/v40 evaluation engine failed');rawp=adapter/'V45_COMPONENT_PRIORITIZED_JOINT_SLOT_RESULT.json';req(rawp.is_file(),'adapter result missing');raw=json.loads(rawp.read_text())
    req(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls'])==4,'exact v31 reproduction failed')
    req(raw['pretruth_graph_sha256']==v40.GRAPH_SHA256 and raw['pretruth_component_sha256']==v40.COMPONENT_SHA256,'v47 geometry changed')
    req(raw['joint_positive_candidate_count']==JOINT_N and raw['nonjoint_candidate_count']==HDB_N-JOINT_N and raw['nonjoint_positions_unchanged'] is True and raw['joint_slot_set_unchanged'] is True,'v47 slot invariants failed')
    sd=dict(raw['order_diagnostics']['sugar']);hd=dict(raw['order_diagnostics']['hdbscan']);req(sd['exact_v31_unchanged'] is True,'Sugar changed');req(hd['v31_order_sha256']==f['v31_order_sha256'] and hd['v45_total_order_sha256']==f['v47_order_sha256'],'evaluator order differs from pretruth freeze')
    rows=[]
    for r0 in raw['hdb_candidate_rows']:
        r=dict(r0);r['v47_rank']=int(r.pop('v45_rank'));r['v47_rank_delta']=int(r.pop('v45_rank_delta'));r['v47_joint_slot_position']=r.pop('v45_joint_slot_position');rows.append(r)
    panels=list(raw['panels']);wins=sum(bool(x['superiority_pair_pass']) for x in panels);req(wins==raw['panel_wins'],'panel win count mismatch');passed=wins==4
    fm={'verdict':'NOT_FROZEN_V47_INHERITANCE_GAP_JOINT_SLOT_FAIL','reference_sha256':None};iref=adapter/'v45_component_prioritized_joint_slot_reference.npz'
    if passed:
        req(iref.is_file(),'passing reference missing');dst=out/'v47_inheritance_gap_joint_slot_reference.npz';shutil.copyfile(iref,dst);fm={'verdict':'PASS_V47_FULL_EXPOSED_INHERITANCE_GAP_JOINT_SLOT_REFERENCE_FREEZE','reference_sha256':v40.v22.sha(dst),'pretruth_graph_sha256':v40.GRAPH_SHA256,'pretruth_component_sha256':v40.COMPONENT_SHA256,'v31_order_sha256':f['v31_order_sha256'],'v47_order_sha256':f['v47_order_sha256'],'joint_gate':'exact #1098/#1139 60-family joint-positive identity set','joint_priority':'(inheritance_gap, exact_v31_rank, family_id)','slot_rule':'permute joint-positive identities only over their exact-v31 occupied positions','sugar_rule':'exact v31 unchanged','in_sample_reference_score_used_for_promotion':False}
    (out/'V47_INHERITANCE_GAP_JOINT_SLOT_MODEL_FREEZE.json').write_text(json.dumps(fm,indent=2,sort_keys=True,allow_nan=False)+'\n')
    result={'scientific_stage':'EXPOSED_SONOTACO_V47_INHERITANCE_GAP_JOINT_SLOT_V1','verdict':'PASS_V47_INHERITANCE_GAP_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V47_INHERITANCE_GAP_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sole_scientific_change':'within the exact #1098/#1139 60-family joint-positive HDB set, permute identities only across their exact-v31 positions, prioritizing smaller frozen inheritance_gap; all 169 nonjoint HDB positions and Sugar remain exact v31','pre_result_frozen_protocol_blob':PROTOCOL_BLOB,'authorizing_diagnostic':'#1139 PASS_V46_JOINT_INHERITANCE_GAP_DIAGNOSTIC','authorizing_diagnostic_run':AUTH_RUN,'authorizing_diagnostic_artifact':AUTH_ART,'authorizing_diagnostic_digest':AUTH_DIGEST,'authorizing_diagnostic_sha256':AUTH_RESULT_SHA,'authorizing_vector_sha256':AUTH_VECTOR_SHA,'authorizing_vector_canonical_sha256':AUTH_VECTOR_CANON,'source_1098_signal_sha256':SIGNAL_SHA,'pretruth_graph_sha256':v40.GRAPH_SHA256,'pretruth_component_sha256':v40.COMPONENT_SHA256,'pretruth_v31_order_sha256':f['v31_order_sha256'],'pretruth_v47_order_sha256':f['v47_order_sha256'],'parent_v31_reproduction_pass':True,'parent_v31_controls':raw['parent_v31_controls'],'feature_dimension':raw['feature_dimension'],'recovery_f1_threshold':raw['recovery_f1_threshold'],'nearest_k':raw['nearest_k'],'v31_distance':raw['v31_distance'],'v31_annual_margin':raw['v31_annual_margin'],'v31_annual_combiner':raw['v31_annual_combiner'],'sugar_rule':'exact v31 unchanged','hdb_joint_gate':'exact #1098/#1139 60-family joint-positive identity set','hdb_joint_priority':'(inheritance_gap, exact_v31_rank, family_id)','hdb_slot_rule':'joint-positive identities permuted only across their exact-v31 positions','joint_positive_candidate_count':JOINT_N,'nonjoint_candidate_count':HDB_N-JOINT_N,'nonjoint_positions_unchanged':True,'joint_slot_set_unchanged':True,'joint_slot_count':JOINT_N,'prefix_diagnostics':raw['prefix_diagnostics'],'panel_wins':wins,'panels':panels,'fold_diagnostics':raw['fold_diagnostics'],'order_diagnostics':{'sugar':sd,'hdbscan':{'family_count':HDB_N,'joint_positive_candidate_count':JOINT_N,'nonjoint_candidate_count':HDB_N-JOINT_N,'moved_up_in_total_order_count':hd['moved_up_in_total_order_count'],'moved_down_in_total_order_count':hd['moved_down_in_total_order_count'],'unchanged_count':hd['unchanged_count'],'v31_order_sha256':f['v31_order_sha256'],'v47_total_order_sha256':f['v47_order_sha256'],'nonjoint_positions_unchanged':True,'joint_slot_set_unchanged':True}},'hdb_candidate_rows':rows,'full_model_freeze':fm,'inheritance_gap_threshold_search':False,'inheritance_gap_quantile_search':False,'inheritance_gap_transform_search':False,'component_size_rule_search':False,'pairwise_dominance_used':False,'boundary_identity_used':False,'boundary_rescue_list_created':False,'top_k_selected':False,'rank_window_selected':False,'promotion_coefficient_search':False,'promotion_bonus_search':False,'promotion_cap_search':False,'slot_expansion':False,'budget_specific_rule':False,'year_specific_rule':False,'sugar_modified':False,'alternate_joint_gate_search':False,'alternate_quality_order_search':False,'radius_search':False,'metric_search':False,'graph_pruning':False,'graph_expansion':False,'component_definition_search':False,'candidate_generation_changed':False,'candidate_membership_changed':False,'feature_search':False,'model_search':False,'k_search':False,'scaling_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'source_quota_selected':False,'oracle_identity_used_for_ranking':False,'truth_aware_group_identity_used_for_ranking':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (out/'V47_INHERITANCE_GAP_JOINT_SLOT_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');shutil.rmtree(adapter);print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'prefix_diagnostics':result['prefix_diagnostics'],'order_diagnostics':result['order_diagnostics'],'full_model_freeze':fm,'panels':panels},indent=2,sort_keys=True,allow_nan=False));return 0

def main()->int:
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    g=sub.add_parser('pretruth');g.add_argument('--sugar-root',type=Path,required=True);g.add_argument('--hdbscan-root',type=Path,required=True);g.add_argument('--output',type=Path,required=True)
    f=sub.add_parser('freeze-order');f.add_argument('--signal-file',type=Path,required=True);f.add_argument('--diagnostic-file',type=Path,required=True);f.add_argument('--vector-file',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    e=sub.add_parser('evaluate');e.add_argument('--sugar-root',type=Path,required=True);e.add_argument('--hdbscan-root',type=Path,required=True);e.add_argument('--truth-root',type=Path,required=True);e.add_argument('--ranker-source',type=Path,required=True);e.add_argument('--graph-file',type=Path,required=True);e.add_argument('--component-file',type=Path,required=True);e.add_argument('--inheritance-diagnostic',type=Path,required=True);e.add_argument('--inheritance-vector',type=Path,required=True);e.add_argument('--order-freeze',type=Path,required=True);e.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='pretruth':return pretruth_mode(a.sugar_root,a.hdbscan_root,a.output)
    if a.mode=='freeze-order':return freeze_order_mode(a.signal_file,a.diagnostic_file,a.vector_file,a.output)
    return evaluate_mode(a.sugar_root,a.hdbscan_root,a.truth_root,a.ranker_source,a.graph_file,a.component_file,a.inheritance_diagnostic,a.inheritance_vector,a.order_freeze,a.output)
if __name__=='__main__':raise SystemExit(main())
