#!/usr/bin/env python3
"""One-shot development of label-free structural fixed4 proposals + multiplicity ranking."""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1,13))
CORPUS='orbittrace-label-free-sparse-support-v6-development'
FIRST_SHORTLIST=64
AUDIT_SHORTLIST=128
MIN_ANCHOR_COUNT=2
MAX_QUARTETS_PER_BIN=512
MIN_SCANNABLE_BINS=24
MIN_FAMILIES=100
MIN_QUALIFIED=72
TOP_K=100
PRIOR_FIXED4_RECOVERY=61
PRIOR_FIXED4_QUALIFIED=90
PRIOR_MULTIPLICITY_RECOVERY=60
MIN_PERSISTENCE_RECOVERY=55
MIN_MULTIPLICITY_ABSOLUTE_RECOVERY=54
BROWN_EQ_TOL=1e-10


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--source-audit-json',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def require(condition:bool,message:str)->None:
    if not condition:
        raise RuntimeError(message)


def label_free_scan_year(year:int,events:list[dict[str,Any]],support:Any,base:Any)->tuple[dict[str,Any],list[dict[str,Any]],list[dict[str,Any]]]:
    """Exact frozen fixed4 anchored-quartet machinery with only the label-dependent threshold removed."""
    event_lookup={str(e['id']):e for e in events}
    passing:list[dict[str,Any]]=[]
    scannable_bins:list[int]=[]
    passing_anchor_count=0
    shortlist_audit_failures=0
    per_bin=[]

    for bin_index in range(36):
        low=bin_index*10.0; high=(bin_index+1)*10.0; center=low+5.0
        anchors=[e for e in events if low <= float(e['sol']) < high]
        pool=[e for e in events if abs(float(base.wrap180(float(e['sol'])-center))) <= 15.0]
        if len(pool) < AUDIT_SHORTLIST or not anchors:
            continue
        scannable_bins.append(bin_index)
        pool_index={str(e['id']):i for i,e in enumerate(pool)}
        features=support.feature_matrix(pool,center,base)
        k_query=min(AUDIT_SHORTLIST,len(pool))
        nn=NearestNeighbors(n_neighbors=k_query,algorithm='auto',metric='euclidean',n_jobs=-1).fit(features)
        anchor_rows=np.asarray([pool_index[str(e['id'])] for e in anchors],dtype=np.int64)
        _,neighbor_indices=nn.kneighbors(features[anchor_rows],return_distance=True)
        local_dedup:dict[tuple[str,...],dict[str,Any]]={}
        bin_anchor_pass=0

        for anchor,candidates_idx in zip(anchors,neighbor_indices):
            candidate_events=[pool[int(i)] for i in candidates_idx if str(pool[int(i)]['id']) != str(anchor['id'])]
            first=candidate_events[:max(3,FIRST_SHORTLIST-1)]
            distances=support.exact_anchor_distances(anchor,first,base)
            order=np.argsort(distances,kind='stable')[:3]
            quartet=[anchor]+[first[int(i)] for i in order]
            score=float(support.quartet_score(quartet,base))

            full=candidate_events[:max(3,AUDIT_SHORTLIST-1)]
            full_distances=support.exact_anchor_distances(anchor,full,base)
            full_order=np.argsort(full_distances,kind='stable')[:3]
            audit_quartet=[anchor]+[full[int(i)] for i in full_order]
            audit_score=float(support.quartet_score(audit_quartet,base))
            ids=tuple(sorted(str(e['id']) for e in quartet))
            audit_ids=tuple(sorted(str(e['id']) for e in audit_quartet))
            if ids != audit_ids or abs(score-audit_score) > 1e-12:
                shortlist_audit_failures += 1
                quartet=audit_quartet; score=audit_score; ids=audit_ids

            passing_anchor_count += 1; bin_anchor_pass += 1
            record=local_dedup.get(ids)
            if record is None:
                local_dedup[ids]={
                    'year':year,'bin':bin_index,'quartet_ids':list(ids),'score':score,
                    'threshold':None,'anchor_count':1,'anchor_ids':[str(anchor['id'])],
                    'label_free_structural_proposal':True,
                }
            else:
                record['anchor_count'] += 1
                record['anchor_ids'].append(str(anchor['id']))
                record['score']=max(float(record['score']),score)

        retained=[r for r in local_dedup.values() if int(r['anchor_count']) >= MIN_ANCHOR_COUNT]
        retained.sort(key=lambda x:(-x['anchor_count'],-x['score'],x['quartet_ids']))
        pre_cap=len(retained)
        retained=retained[:MAX_QUARTETS_PER_BIN]
        count=len(retained)
        for rank,record in enumerate(retained,1):
            rank_fraction=(rank-0.5)/max(1,count)
            record['bin_rank']=rank
            record['bin_count']=count
            record['bin_strength']=-math.log10(rank_fraction)
        passing.extend(retained)
        per_bin.append({
            'bin':bin_index,'anchors':len(anchors),'pool':len(pool),'anchored_quartets_examined':bin_anchor_pass,
            'unique_quartets_before_anchor_gate':len(local_dedup),'anchor_multiplicity_pass_before_cap':pre_cap,
            'retained_after_fixed_512_cap':count,
        })
        print(f'label-free-v6 {year} bin {bin_index}: anchors={len(anchors)} retained={count}',flush=True)

    passing.sort(key=lambda x:(x['bin'],x['bin_rank'],x['quartet_ids']))
    components=support.component_records(year,passing,event_lookup)
    audit={
        'year':year,'scan_events':len(events),'scannable_bins':scannable_bins,'scannable_bin_count':len(scannable_bins),
        'passing_anchor_count':passing_anchor_count,'retained_quartets':len(passing),'components':len(components),
        'shortlist_audit_failures':shortlist_audit_failures,'per_bin':per_bin,
        'calibration_events_used':0,'source_labels_used_for_proposals':False,'score_threshold_applied':False,
        'min_anchor_count':MIN_ANCHOR_COUNT,'max_quartets_per_bin':MAX_QUARTETS_PER_BIN,
    }
    return audit,passing,components


def compact(m:dict[str,Any])->dict[str,Any]:
    return {k:v for k,v in m.items() if k!='per_label'}


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    source_audit=json.loads(args.source_audit_json.read_text())
    require(source_audit['verdict']=='PASS_WAVELET_CATALOGUE_V3_SOURCE_AUDIT','frozen source audit did not pass')
    require(source_audit['development_source_sha256']=='ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51','runtime source changed')
    require(source_audit['support_source_sha256']=='fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62','support source changed')
    require(source_audit['target_information_present'] is False,'target information entered source audit')
    require(source_audit['labels_enter_candidate_generation'] is False,'frozen source label boundary changed')

    require(all(mult.v3.self_test().values()),'multi-anchor v3 self-test failed')
    require(all(mult.brown.self_test().values()),'Brown self-test failed')
    runtime=mult.load_frozen_runtime()
    support=runtime.load_support_module(args.support_source_parts)

    # Restore/declare only the exact development panel and raw fixed4 family-ranking state.
    support.YEARS=YEARS
    support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS=CORPUS
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    require(int(support.MIN_FAMILY_YEARS)==2,'family-year minimum changed')
    require(abs(float(support.FAMILY_LINK_RADIUS)-1.5)<1e-15,'family link radius changed')
    require(int(support.MIN_COMPONENT_EVENTS)==4 and int(support.MIN_COMPONENT_QUARTETS)==2,'component gates changed')
    require(int(support.SHORTLIST_K)==FIRST_SHORTLIST and int(support.AUDIT_SHORTLIST_K)==AUDIT_SHORTLIST,'shortlists changed')
    require(int(support.MIN_ANCHOR_COUNT)==MIN_ANCHOR_COUNT and int(support.MAX_QUARTETS_PER_BIN)==MAX_QUARTETS_PER_BIN,'proposal cap/gate changed')
    for name in ('feature_matrix','exact_anchor_distances','quartet_score','component_records','build_families'):
        require(hasattr(support,name),f'frozen support missing {name}')

    setattr(args,'fixed4_baseline_json',args.source_audit_json)
    _candidate,base,_scorer=support.load_sources(args)
    require(abs(float(getattr(_candidate,'CANDIDATE_SCALE',4.0))-4.0)<1e-15,'fixed4 candidate scale changed')

    # FIRST DEVELOPMENT DATA ACCESS. The target interval is removed inside the guarded frozen parser before labels.
    scan_by_year,_calibration_by_year,hidden_labels,catalogue_sources=support.parse_catalogue(base)
    require(sorted(scan_by_year)==list(YEARS),'development year universe changed')
    require([s['key'] for s in catalogue_sources]==list(MONTH_KEYS),'development monthly sources changed')

    components=[]; scan_audits=[]; passing_counts={}
    for year in YEARS:
        audit,passing,year_components=label_free_scan_year(year,scan_by_year[year],support,base)
        scan_audits.append(audit); passing_counts[str(year)]=len(passing); components.extend(year_components)
        print(f'label-free-v6 year {year}: quartets={len(passing)} components={len(year_components)}',flush=True)

    families,support_rankings=support.build_families(components,base)
    persistence_order=[str(x) for x in support_rankings['persistence']]
    family_ids=[str(f['family_id']) for f in families]
    require(set(persistence_order)==set(family_ids) and len(persistence_order)==len(family_ids),'persistence family universe mismatch')

    # Reuse the exact multiplicity-v5 scoring/ranking/evaluation implementation with only the development years substituted.
    mult.YEARS=YEARS; mult.MONTH_KEYS=MONTH_KEYS; mult.TOP_K=TOP_K
    scored,scoring_summary=mult.score_families(families,scan_by_year,runtime,base)
    require(len(scored)==len(families),'not every family scored')
    rankings={
        'multiplicity':mult.rank_scored(scored,'multiplicity'),
        'brown':mult.rank_scored(scored,'brown'),
        'v3':mult.rank_scored(scored,'v3'),
        'label_free_persistence':persistence_order,
    }

    # FIRST SHOWER-LABEL USE FOR THIS ARCHITECTURE: all proposal generation and rankings are already frozen above.
    metrics_full={name:mult.evaluate_order(hidden_labels,families,order) for name,order in rankings.items()}
    metrics={name:compact(v) for name,v in metrics_full.items()}
    correlations={
        'multiplicity_brown_spearman':mult.rank_spearman(rankings['multiplicity'],rankings['brown']),
        'multiplicity_v3_spearman':mult.rank_spearman(rankings['multiplicity'],rankings['v3']),
        'multiplicity_persistence_spearman':mult.rank_spearman(rankings['multiplicity'],rankings['label_free_persistence']),
    }
    top100_overlaps={
        'multiplicity_brown':mult.overlap100(rankings['multiplicity'],rankings['brown']),
        'multiplicity_v3':mult.overlap100(rankings['multiplicity'],rankings['v3']),
        'multiplicity_persistence':mult.overlap100(rankings['multiplicity'],rankings['label_free_persistence']),
    }

    qualified=int(metrics['multiplicity']['qualified_matches'])
    same_qualified=len({int(v['qualified_matches']) for v in metrics.values()})==1
    persistence_recovery=int(metrics['label_free_persistence']['recovered_at_100'])
    multiplicity_recovery=int(metrics['multiplicity']['recovered_at_100'])
    brown_recovery=int(metrics['brown']['recovered_at_100'])
    required_vs_persistence=int(math.ceil(0.90*persistence_recovery))
    exact_years=all(sorted(int(y) for y in f['years'])==list(YEARS) for f in families)
    scannable=all(int(a['scannable_bin_count'])>=MIN_SCANNABLE_BINS for a in scan_audits)
    exact_episode_sizes=scoring_summary['episode_sizes']==[128] if families else False

    integrity_gates={
        'frozen_source_and_self_tests':True,
        'exact_target_excluded_2022_2023_panel':sorted(scan_by_year)==list(YEARS) and [s['key'] for s in catalogue_sources]==list(MONTH_KEYS),
        'zero_label_dependent_calibration_events':all(a['calibration_events_used']==0 and a['source_labels_used_for_proposals'] is False for a in scan_audits),
        'no_score_threshold_applied':all(a['score_threshold_applied'] is False for a in scan_audits),
        'at_least_24_scannable_bins_each_year':scannable,
        'all_families_span_both_years':exact_years,
        'all_local_episode_sizes_exact_128':exact_episode_sizes,
        'brown_equivalence_within_1e_10':float(scoring_summary['max_brown_equivalence_difference'])<=BROWN_EQ_TOL,
        'at_least_100_recurrent_families':len(families)>=MIN_FAMILIES,
        'at_least_72_qualified_known_showers':qualified>=MIN_QUALIFIED and same_qualified,
    }
    scientific_gates={
        'label_free_persistence_recovered_at_100_at_least_55':persistence_recovery>=MIN_PERSISTENCE_RECOVERY,
        'multiplicity_recovers_at_least_one_more_than_brown':multiplicity_recovery>=brown_recovery+1,
        'multiplicity_recovers_at_least_90pct_of_label_free_persistence':multiplicity_recovery>=required_vs_persistence,
        'multiplicity_recovered_at_100_at_least_54':multiplicity_recovery>=MIN_MULTIPLICITY_ABSOLUTE_RECOVERY,
        'multiplicity_top100_precision_at_least_050':float(metrics['multiplicity']['top100_dominant_precision'])>=0.50,
    }
    verdict='PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT' if all(integrity_gates.values()) and all(scientific_gates.values()) else 'FAIL_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT'

    family_sizes=[int(f['event_count']) for f in families]
    result={
        'verdict':verdict,
        'configuration':{
            'years':list(YEARS),'blind_exclusion':[20.0,55.0],'corpus':CORPUS,
            'proposal_generator':'exact fixed4 anchored-quartet structural ranking with calibrated score threshold removed',
            'first_shortlist':FIRST_SHORTLIST,'audit_shortlist':AUDIT_SHORTLIST,'min_anchor_count':MIN_ANCHOR_COUNT,
            'max_quartets_per_bin':MAX_QUARTETS_PER_BIN,'family_link_radius':1.5,
            'primary_ranking':'worst-year multiplicity descending, geometric-mean multiplicity descending, family id',
            'multiplicity':'(multi-anchor-v3-energy / Brown-peak)^2','episode_size':128,'top_k':TOP_K,
            'no_source_labels_in_proposal_generation':True,'no_calibration_threshold':True,'no_threshold_search':True,
            'no_cap_search':True,'no_weight_search':True,'no_rrf':True,
        },
        'catalogue_sources':catalogue_sources,'scan_audits':scan_audits,'retained_quartet_counts':passing_counts,
        'family_count':len(families),
        'family_size_summary':{
            'min':min(family_sizes) if family_sizes else None,'median':float(np.median(family_sizes)) if family_sizes else None,
            'p95':float(np.quantile(family_sizes,0.95)) if family_sizes else None,'max':max(family_sizes) if family_sizes else None,
        },
        'family_scoring_summary':scoring_summary,'metrics':metrics,'correlations':correlations,'top100_overlaps':top100_overlaps,
        'integrity_gates':integrity_gates,'scientific_gates':scientific_gates,
        'required_multiplicity_recovery_vs_persistence':required_vs_persistence,
        'historical_reference':{'fixed4_calibrated_qualified':PRIOR_FIXED4_QUALIFIED,'fixed4_calibrated_recovered100':PRIOR_FIXED4_RECOVERY,'multiplicity_prior_recovered100':PRIOR_MULTIPLICITY_RECOVERY},
        'claim_boundary':'Development-only label-free proposal/ranking architecture on already-exposed target-excluded 2022-2023 GMN data. Labels were consulted only after rankings were frozen. No OrbitTrace target information or 20-55 degree target-region event entered the method.',
    }
    (args.output/'label_free_sparse_support_v6_development.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'label_free_sparse_support_v6_rankings.json').write_text(json.dumps(rankings,indent=2)+'\n')
    (args.output/'label_free_sparse_support_v6_families.json.gz').write_bytes(gzip.compress(json.dumps(families,separators=(',',':')).encode()))
    (args.output/'label_free_sparse_support_v6_scores.json.gz').write_bytes(gzip.compress(json.dumps(scored,separators=(',',':')).encode()))
    (args.output/'label_free_sparse_support_v6_evaluation.json.gz').write_bytes(gzip.compress(json.dumps(metrics_full,separators=(',',':')).encode()))
    lines=[
        '# OrbitTrace label-free sparse-support multiplicity v6 development','',f'Verdict: **`{verdict}`**','',
        f'- recurrent label-free families: **{len(families)}**',f'- qualified known showers: **{qualified}**',
        f'- label-free persistence recovered@100: **{persistence_recovery}**; precision: **{metrics["label_free_persistence"]["top100_dominant_precision"]:.4f}**',
        f'- multiplicity recovered@100: **{multiplicity_recovery}**; precision: **{metrics["multiplicity"]["top100_dominant_precision"]:.4f}**',
        f'- Brown recovered@100: **{brown_recovery}**; precision: **{metrics["brown"]["top100_dominant_precision"]:.4f}**',
        f'- total-v3 recovered@100: **{metrics["v3"]["recovered_at_100"]}**',
        f'- required multiplicity recovery for 90% persistence gate: **{required_vs_persistence}**',
        f'- multiplicity vs persistence Spearman: **{correlations["multiplicity_persistence_spearman"]:.4f}**',
        f'- family event-count median / p95 / max: **{result["family_size_summary"]["median"]} / {result["family_size_summary"]["p95"]} / {result["family_size_summary"]["max"]}**','',
        'No source shower label entered proposal generation. The 20°–55° target interval remained excluded before label access.'
    ]
    (args.output/'LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
