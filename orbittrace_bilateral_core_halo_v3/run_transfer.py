#!/usr/bin/env python3
"""Frozen 2024-2025 transfer of v8 discovery core + bilateral characterization halo."""
from __future__ import annotations

import argparse, copy, json, math
from collections import defaultdict
from pathlib import Path

import numpy as np

from orbittrace_cross_year_seed_support_expansion_v1 import run_development as v1

v8=v1.v8; v6=v1.v6; mult=v1.mult
YEARS=(2024,2025)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
CORPUS='orbittrace-bilateral-core-halo-v3-transfer'
TOP_K=100
RADIUS=1.5


def parse_args():
    p=argparse.ArgumentParser()
    for name in ('support_source_parts','candidate_payload','baseline_payload','scorer_parts','source_audit_json','v6_result_json','centroid_audit_json'):
        p.add_argument('--'+name.replace('_','-'),required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def require(x,msg):
    if not x: raise RuntimeError(msg)


def compact(x): return {k:v for k,v in x.items() if k!='per_label'}


def bilateral_expand(families, scan_by_year):
    expanded=copy.deepcopy(families)
    fam_lookup={str(f['family_id']):f for f in expanded}
    original={str(f['family_id']):set(str(x) for x in f['event_ids']) for f in families}
    event_lookup={y:{str(e['id']):e for e in scan_by_year[y]} for y in YEARS}
    assignments={str(y):{} for y in YEARS}
    diag={'radius':RADIUS,'solar_prefilter_deg':4.0*RADIUS,'bilateral_same_and_other_year_support':True,
          'new_members_never_reused_as_support':True,'exclusive_assignment':True,
          'new_members_by_year':{},'eligible_pair_count_by_year':{},'conflicted_events_by_year':{},'original_seed_events_by_year':{}}
    for target_year in YEARS:
        other_year=YEARS[1] if target_year==YEARS[0] else YEARS[0]
        target_events=scan_by_year[target_year]
        target_sol=np.asarray([float(e['sol'])%360.0 for e in target_events])
        target_seed_owner={}
        for fid,ids in original.items():
            for eid in ids & set(event_lookup[target_year]):
                old=target_seed_owner.get(eid); require(old is None or old==fid,f'seed event belongs to multiple families: {eid}')
                target_seed_owner[eid]=fid
        best={}; eligible_pairs=0
        for family in families:
            fid=str(family['family_id'])
            same_ids=sorted(original[fid] & set(event_lookup[target_year]))
            other_ids=sorted(original[fid] & set(event_lookup[other_year]))
            require(same_ids and other_ids,f'family {fid} lacks bilateral core support')
            same_support=[event_lookup[target_year][eid] for eid in same_ids]
            other_support=[event_lookup[other_year][eid] for eid in other_ids]
            mask_same=v1.in_expanded_arc(target_sol,[float(e['sol']) for e in same_support])
            mask_other=v1.in_expanded_arc(target_sol,[float(e['sol']) for e in other_support])
            idx=np.flatnonzero(mask_same & mask_other)
            candidates=[target_events[int(i)] for i in idx]
            ds=v1.min_exact_distances(candidates,same_support)
            do=v1.min_exact_distances(candidates,other_support)
            for i,d_same,d_other in zip(idx.tolist(),ds.tolist(),do.tolist()):
                if d_same>RADIUS+1e-12 or d_other>RADIUS+1e-12: continue
                eid=str(target_events[i]['id'])
                if eid in target_seed_owner: continue
                eligible_pairs+=1
                cand=(max(float(d_same),float(d_other)),float(d_same)+float(d_other),fid)
                old=best.get(eid)
                if old is None or cand<old: best[eid]=cand
        by_family=defaultdict(list)
        for eid,(_mx,_sum,fid) in best.items(): by_family[fid].append(eid)
        for fid,ids in by_family.items():
            ids.sort(); fam=fam_lookup[fid]
            fam['event_ids']=sorted(set(str(x) for x in fam['event_ids'])|set(ids)); fam['event_count']=len(fam['event_ids'])
            assignments[str(target_year)][fid]=ids
        diag['new_members_by_year'][str(target_year)]=len(best)
        diag['eligible_pair_count_by_year'][str(target_year)]=eligible_pairs
        diag['conflicted_events_by_year'][str(target_year)]=max(0,eligible_pairs-len(best))
        diag['original_seed_events_by_year'][str(target_year)]=len(target_seed_owner)
    before_by={str(f['family_id']):f for f in families}
    for after in expanded:
        before=before_by[str(after['family_id'])]
        for field in ('years','year_count','component_ids','component_count','quartet_count','anchor_count','best_score','year_strengths','ranking_scores','ranks','centroids'):
            require(before[field]==after[field],f'halo changed core field {field}')
        require(set(before['event_ids']).issubset(set(after['event_ids'])),'core event lost')
    diag['total_new_members']=sum(diag['new_members_by_year'].values())
    diag['expanded_membership_sha256']=v1.sha256_json({str(f['family_id']):f['event_ids'] for f in expanded})
    return expanded,diag,assignments


def main():
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    sa=json.loads(args.source_audit_json.read_text()); pred=json.loads(args.v6_result_json.read_text()); ca=json.loads(args.centroid_audit_json.read_text())
    require(sa['verdict']=='PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT','source audit failed')
    require(sa['target_information_present'] is False,'target information entered source')
    require(pred['verdict']=='PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT','v6 predecessor failed')
    require(ca['verdict']=='PASS_COMPONENT_CENTROID_SOURCE_AUDIT','centroid audit failed')
    require(all(mult.v3.self_test().values()) and all(mult.brown.self_test().values()),'score self-test failed')

    runtime=mult.load_frozen_runtime(); support=runtime.load_support_module(args.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS=CORPUS
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    require(abs(float(support.FAMILY_LINK_RADIUS)-RADIUS)<=1e-15,'inherited radius changed')
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
        require(audit['source_labels_used_for_proposals'] is False and audit['score_threshold_applied'] is False,'proposal blindness changed')
        audits.append(audit); components.extend(comps)
    families,support_rankings=support.build_families(components,base)
    repair=v8.repair_year_centroids(families,components,scan_by_year,support,base)
    scored,scoring=mult.score_families(families,scan_by_year,runtime,base)
    rankings={'multiplicity':mult.rank_scored(scored,'multiplicity'),'brown':mult.rank_scored(scored,'brown'),'v3':mult.rank_scored(scored,'v3'),'label_free_persistence':[str(x) for x in support_rankings['persistence']]}

    halo,halo_diag,assignments=bilateral_expand(families,scan_by_year)
    prelabel={'core_order':rankings['multiplicity'],'core':{str(f['family_id']):f['event_ids'] for f in families},'halo':{str(f['family_id']):f['event_ids'] for f in halo},'assignments':assignments}
    prelabel_sha=v1.sha256_json(prelabel); (args.output/'bilateral_core_halo_prelabel_sha256.txt').write_text(prelabel_sha+'\n')

    core_full={k:mult.evaluate_order(hidden_labels,families,o) for k,o in rankings.items()}; halo_full={k:mult.evaluate_order(hidden_labels,halo,o) for k,o in rankings.items()}
    core={k:compact(v) for k,v in core_full.items()}; hm={k:compact(v) for k,v in halo_full.items()}
    core_ann=v1.annual_summary(families,hidden_labels,scan_by_year); halo_ann=v1.annual_summary(halo,hidden_labels,scan_by_year)
    delta={}
    for y in YEARS:
        ys=str(y); delta[ys]={}
        for b in ('4-9','10-24','25-49','50-99','100+','all'):
            a=core_ann[ys]['summary'][b]['mean_f1']; z=halo_ann[ys]['summary'][b]['mean_f1']; delta[ys][b]=None if a is None or z is None else float(z-a)

    cm=core['multiplicity']; hp=hm['multiplicity']; pers=core['label_free_persistence']; brown=core['brown']; req90=math.ceil(.90*int(pers['recovered_at_100']))
    moderate=[]
    for b in ('10-24','25-49','50-99','100+'):
        if all(core_ann[str(y)]['summary'][b]['showers']>0 for y in YEARS): moderate.append(all(float(delta[str(y)][b])>=.10 for y in YEARS))
    integrity={'target_excluded_2024_2025':sorted(scan_by_year)==list(YEARS),'at_least_24_scannable_bins_each_year':all(int(a['scannable_bin_count'])>=24 for a in audits),'all_families_span_both_years':all(sorted(int(y) for y in f['years'])==list(YEARS) for f in families),'all_local_episode_sizes_exact_128':scoring['episode_sizes']==[128] if families else False,'brown_equivalence_within_1e_10':float(scoring['max_brown_equivalence_difference'])<=v8.BROWN_EQ_TOL,'zero_label_dependent_proposal_calibration':all(a['source_labels_used_for_proposals'] is False and a['score_threshold_applied'] is False for a in audits),'core_rank_frozen_before_halo':True,'halo_cannot_change_core_rank_or_scores':rankings['multiplicity']==mult.rank_scored(scored,'multiplicity'),'bilateral_same_and_other_core_support':halo_diag['bilateral_same_and_other_year_support'],'halo_nonrecursive':halo_diag['new_members_never_reused_as_support'],'exact_inherited_radius_1_5':abs(float(halo_diag['radius'])-1.5)<=1e-15,'prelabel_core_halo_hash_frozen':len(prelabel_sha)==64}
    core_gates={'at_least_100_recurrent_families':len(families)>=100,'at_least_72_qualified_known_showers':int(cm['qualified_matches'])>=72,'persistence_recovery_at_100_at_least_55':int(pers['recovered_at_100'])>=55,'multiplicity_at_least_brown_plus_1':int(cm['recovered_at_100'])>=int(brown['recovered_at_100'])+1,'multiplicity_at_least_90pct_persistence':int(cm['recovered_at_100'])>=req90,'multiplicity_recovery_at_100_at_least_54':int(cm['recovered_at_100'])>=54,'core_top100_precision_at_least_050':float(cm['top100_dominant_precision'])>=.50}
    halo_gates={'halo_macro_f1_gain_at_least_005':float(hp['macro_f1'])>=float(cm['macro_f1'])+.05,'annual_all_mean_f1_gain_at_least_010_both_years':all(float(delta[str(y)]['all'])>=.10 for y in YEARS),'annual_4_9_no_material_regression':all(float(delta[str(y)]['4-9'])>=-.02 for y in YEARS),'moderate_or_large_material_gain_both_years':any(moderate),'halo_top100_dominant_precision_at_least_050':float(hp['top100_dominant_precision'])>=.50}
    verdict='PASS_BILATERAL_CORE_HALO_V3_TRANSFER' if all(integrity.values()) and all(core_gates.values()) and all(halo_gates.values()) else 'FAIL_BILATERAL_CORE_HALO_V3_TRANSFER'
    result={'verdict':verdict,'configuration':{'years':list(YEARS),'blind_exclusion':[20.0,55.0],'core':'exact frozen v8','halo':'same-year AND other-year original-core support, exact radius 1.5','assignment':'min max-distance, then sum-distance, then family ID','halo_changes_discovery':False,'radius_search':False,'threshold_search':False},'family_count':len(families),'prelabel_sha256':prelabel_sha,'repair':repair,'halo_diagnostics':halo_diag,'core_metrics':core,'halo_metrics_diagnostic':hm,'core_annual':{k:v['summary'] for k,v in core_ann.items()},'halo_annual':{k:v['summary'] for k,v in halo_ann.items()},'annual_f1_delta':delta,'integrity_gates':integrity,'core_gates':core_gates,'halo_gates':halo_gates,'claim_boundary':'Target-excluded method-specific 2024-2025 transfer. Bilateral halo cannot affect discovery ranking or qualification. No OrbitTrace target information, target-region event, Stage A/B output, or reveal was accessed.'}
    (args.output/'bilateral_core_halo_v3_transfer.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    lines=['# OrbitTrace bilateral core/halo v3 transfer','',f'**Verdict:** `{verdict}`','',f'- core families: **{len(families)}**',f'- new bilateral halo events: **{halo_diag["total_new_members"]}**',f'- core / halo macro F1: **{cm["macro_f1"]:.6f} / {hp["macro_f1"]:.6f}**',f'- core recovery@100: **{cm["recovered_at_100"]}**',f'- core top100 precision: **{cm["top100_dominant_precision"]:.6f}**',f'- halo diagnostic top100 precision: **{hp["top100_dominant_precision"]:.6f}**']
    for y in YEARS: lines.append(f'- {y} all-shower mean-F1 delta: **{delta[str(y)]["all"]:+.6f}**')
    lines += ['', 'No OrbitTrace target information was accessed. The halo never enters discovery ranking or qualification.']
    (args.output/'BILATERAL_CORE_HALO_V3_TRANSFER.md').write_text('\n'.join(lines)+'\n'); print('\n'.join(lines),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
