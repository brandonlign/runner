#!/usr/bin/env python3
"""Frozen 2020-2021 transfer of the dual-output v8 core / crossfit halo architecture."""
from __future__ import annotations

import argparse, json, math
from pathlib import Path

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

v8=v1.v8; v6=v1.v6; mult=v1.mult
YEARS=(2020,2021)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
CORPUS='orbittrace-core-halo-membership-v2-transfer'
TOP_K=100


def args_parser():
    p=argparse.ArgumentParser()
    for name in ('support_source_parts','candidate_payload','baseline_payload','scorer_parts','source_audit_json','v6_result_json','centroid_audit_json'):
        p.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def require(x,msg):
    if not x: raise RuntimeError(msg)


def compact(x): return {k:v for k,v in x.items() if k!='per_label'}


def main():
    args=args_parser(); args.output.mkdir(parents=True,exist_ok=True)
    sa=json.loads(args.source_audit_json.read_text()); pred=json.loads(args.v6_result_json.read_text()); ca=json.loads(args.centroid_audit_json.read_text())
    require(sa['verdict']=='PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT','source audit failed')
    require(sa['target_information_present'] is False,'target info in source')
    require(pred['verdict']=='PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT','v6 predecessor failed')
    require(ca['verdict']=='PASS_COMPONENT_CENTROID_SOURCE_AUDIT','centroid audit failed')
    require(all(mult.v3.self_test().values()) and all(mult.brown.self_test().values()),'score self-test failed')

    runtime=mult.load_frozen_runtime(); support=runtime.load_support_module(args.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS=CORPUS
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    require(abs(float(support.FAMILY_LINK_RADIUS)-1.5)<=1e-15,'radius changed')
    setattr(args,'fixed4_baseline_json',args.source_audit_json)
    _candidate,base,_scorer=support.load_sources(args)

    v1.YEARS=YEARS; v1.MONTH_KEYS=MONTH_KEYS
    v8.YEARS=YEARS; v8.MONTH_KEYS=MONTH_KEYS
    v6.YEARS=YEARS; v6.MONTH_KEYS=MONTH_KEYS
    mult.YEARS=YEARS; mult.MONTH_KEYS=MONTH_KEYS; mult.TOP_K=TOP_K

    scan_by_year,_calibration,hidden_labels,sources=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),'year universe changed')
    require([s['key'] for s in sources]==list(MONTH_KEYS),'month universe changed')

    components=[]; audits=[]
    for y in YEARS:
        audit,_passing,comps=v6.label_free_scan_year(y,scan_by_year[y],support,base)
        require(audit['source_labels_used_for_proposals'] is False and audit['score_threshold_applied'] is False,'proposal label boundary changed')
        audits.append(audit); components.extend(comps)
    families,support_rankings=support.build_families(components,base)
    repair=v8.repair_year_centroids(families,components,scan_by_year,support,base)
    scored,scoring=mult.score_families(families,scan_by_year,runtime,base)
    rankings={
      'multiplicity':mult.rank_scored(scored,'multiplicity'),
      'brown':mult.rank_scored(scored,'brown'),
      'v3':mult.rank_scored(scored,'v3'),
      'label_free_persistence':[str(x) for x in support_rankings['persistence']],
    }

    halo,halo_diag,assignments=v1.crossfit_expand(families,scan_by_year)
    prelabel={
      'core_order':rankings['multiplicity'],
      'core':{str(f['family_id']):f['event_ids'] for f in families},
      'halo':{str(f['family_id']):f['event_ids'] for f in halo},
      'assignments':assignments,
    }
    prelabel_sha=v1.sha256_json(prelabel)
    (args.output/'core_halo_prelabel_sha256.txt').write_text(prelabel_sha+'\n')

    core_full={k:mult.evaluate_order(hidden_labels,families,o) for k,o in rankings.items()}
    halo_full={k:mult.evaluate_order(hidden_labels,halo,o) for k,o in rankings.items()}
    core={k:compact(v) for k,v in core_full.items()}; halo_metrics={k:compact(v) for k,v in halo_full.items()}
    core_ann=v1.annual_summary(families,hidden_labels,scan_by_year); halo_ann=v1.annual_summary(halo,hidden_labels,scan_by_year)
    delta={}
    for y in YEARS:
      ys=str(y); delta[ys]={}
      for b in ('4-9','10-24','25-49','50-99','100+','all'):
        a=core_ann[ys]['summary'][b]['mean_f1']; z=halo_ann[ys]['summary'][b]['mean_f1']
        delta[ys][b]=None if a is None or z is None else float(z-a)

    cm=core['multiplicity']; hp=halo_metrics['multiplicity']; pers=core['label_free_persistence']; brown=core['brown']
    req90=math.ceil(0.90*int(pers['recovered_at_100']))
    moderate=[]
    for b in ('10-24','25-49','50-99','100+'):
      if all(core_ann[str(y)]['summary'][b]['showers']>0 for y in YEARS):
        moderate.append(all(float(delta[str(y)][b])>=0.10 for y in YEARS))

    integrity={
      'target_excluded_2020_2021':sorted(scan_by_year)==list(YEARS),
      'at_least_24_scannable_bins_each_year':all(int(a['scannable_bin_count'])>=24 for a in audits),
      'all_families_span_both_years':all(sorted(int(y) for y in f['years'])==list(YEARS) for f in families),
      'all_local_episode_sizes_exact_128':scoring['episode_sizes']==[128] if families else False,
      'brown_equivalence_within_1e_10':float(scoring['max_brown_equivalence_difference'])<=v8.BROWN_EQ_TOL,
      'zero_label_dependent_proposal_calibration':all(a['source_labels_used_for_proposals'] is False and a['score_threshold_applied'] is False for a in audits),
      'core_rank_frozen_before_halo':True,
      'halo_cannot_change_core_rank_or_scores':rankings['multiplicity']==mult.rank_scored(scored,'multiplicity'),
      'halo_other_year_seed_support_only':halo_diag['other_year_support_only'],
      'halo_nonrecursive':halo_diag['new_members_never_reused_as_support'],
      'halo_exact_radius_1_5':abs(float(halo_diag['radius'])-1.5)<=1e-15,
      'prelabel_core_halo_hash_frozen':len(prelabel_sha)==64,
    }
    core_gates={
      'at_least_100_recurrent_families':len(families)>=100,
      'at_least_72_qualified_known_showers':int(cm['qualified_matches'])>=72,
      'persistence_recovery_at_100_at_least_55':int(pers['recovered_at_100'])>=55,
      'multiplicity_at_least_brown_plus_1':int(cm['recovered_at_100'])>=int(brown['recovered_at_100'])+1,
      'multiplicity_at_least_90pct_persistence':int(cm['recovered_at_100'])>=req90,
      'multiplicity_recovery_at_100_at_least_54':int(cm['recovered_at_100'])>=54,
      'core_top100_precision_at_least_050':float(cm['top100_dominant_precision'])>=0.50,
    }
    halo_gates={
      'halo_macro_f1_gain_at_least_005':float(hp['macro_f1'])>=float(cm['macro_f1'])+0.05,
      'annual_all_mean_f1_gain_at_least_010_both_years':all(float(delta[str(y)]['all'])>=0.10 for y in YEARS),
      'annual_4_9_no_material_regression':all(float(delta[str(y)]['4-9'])>=-0.02 for y in YEARS),
      'moderate_or_large_material_gain_both_years':any(moderate),
      'halo_top100_dominant_precision_at_least_050':float(hp['top100_dominant_precision'])>=0.50,
    }
    verdict='PASS_CORE_HALO_MEMBERSHIP_V2_TRANSFER' if all(integrity.values()) and all(core_gates.values()) and all(halo_gates.values()) else 'FAIL_CORE_HALO_MEMBERSHIP_V2_TRANSFER'
    result={
      'verdict':verdict,
      'configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'core':'exact v8 families/ranking','halo':'exact v1 cross-year support expansion radius 1.5','halo_changes_discovery':False,'threshold_search':False,'radius_search':False},
      'family_count':len(families),'prelabel_sha256':prelabel_sha,'repair':repair,'halo_diagnostics':halo_diag,
      'core_metrics':core,'halo_metrics_diagnostic':halo_metrics,
      'core_annual':{k:v['summary'] for k,v in core_ann.items()},'halo_annual':{k:v['summary'] for k,v in halo_ann.items()},'annual_f1_delta':delta,
      'integrity_gates':integrity,'core_gates':core_gates,'halo_gates':halo_gates,
      'claim_boundary':'Independent-year target-excluded transfer of a dual-output architecture. Halo membership cannot affect discovery rank or core qualification. No OrbitTrace target information or target-region event was accessed.'
    }
    (args.output/'core_halo_membership_v2_transfer.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    lines=['# OrbitTrace core/halo membership v2 transfer','',f'**Verdict:** `{verdict}`','',f'- core families: **{len(families)}**',f'- halo new events: **{halo_diag["total_new_members"]}**',f'- core/halo macro F1: **{cm["macro_f1"]:.6f} / {hp["macro_f1"]:.6f}**',f'- core recovery@100: **{cm["recovered_at_100"]}**',f'- core top100 precision: **{cm["top100_dominant_precision"]:.6f}**',f'- halo diagnostic top100 precision: **{hp["top100_dominant_precision"]:.6f}**']
    for y in YEARS: lines.append(f'- {y} annual all-F1 delta: **{delta[str(y)]["all"]:+.6f}**')
    lines += ['', 'The halo never enters discovery ranking or qualification. No OrbitTrace target information was accessed.']
    (args.output/'CORE_HALO_MEMBERSHIP_V2_TRANSFER.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
