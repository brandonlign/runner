#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_p19_subthreshold_recurrence import run_development as p19
from orbittrace_p20_recurrent_isolated_quartet import run_development as p20
from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application as urc_application
from orbittrace_unified_recurrent_catalogue_lab_v2 import run_lab as urc_v2
from orbittrace_v15_canonical_application_v1 import application as v15_application
from orbittrace_v16_v15_joint_conformal_membership_v1 import expand_candidate as jc
from orbittrace_v17_urc_v15_density_port_v1 import run_candidate_pretruth as v17
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import prepare_pretruth as v22prep
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_support_base, require

YEARS = (2013, 2014)
TOP_K = 100
BASE_DIM = 71
POST_DIM = 16
COMBINED_DIM = BASE_DIM + POST_DIM
EXPECTED_RANKER_SHA = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
EXPECTED_MODEL_SHA = 'ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909'
EXPECTED = {
    'sugar': {
        'base_feature_sha256': '486c247d12bd769f281444b4b3b9adf0ec3cd517dc88485f3deccffd8e395f1f',
        'centroid_sha256': '6f920ede2497b0cd1a5a8e303a6e87a6217fc8919deb4c81b131b1e5a5f20e91',
        'expanded_family_sha256': '911bbc1d763f79ee661863a6d5c2cc98d97d0debd276e64461d45a5447c7bfeb',
    },
    'hdbscan': {
        'base_feature_sha256': 'd25f5e7899b2ab5dba7e7c1d1f6269896fee34714492bb53264c659db32c310d',
        'centroid_sha256': '90504db13491ba83a4dffb35892d3bd87764827b99e497bc56c80425700eab79',
        'expanded_family_sha256': '7137a5c0892e5d316db38915ff164f2a8fb6e8fbe8e0ed2cfa063097968a1895',
    },
}

POST_FEATURE_NAMES = (
    'expanded_member_count_min_year',
    'expanded_member_count_max_year',
    'expanded_member_count_year_balance',
    'expanded_member_distance_median',
    'expanded_member_distance_q90',
    'expanded_member_distance_max',
    'expanded_year_q90_distance_max',
    'log1p_core_member_count',
    'log1p_added_member_count',
    'added_to_core_ratio',
    'accepted_d2_median',
    'accepted_d2_q90',
    'accepted_trajectory_residual_median',
    'accepted_trajectory_residual_q90',
    'accepted_neglog_joint_p_median',
    'accepted_neglog_joint_p_q90',
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(',', ':')).encode())
    h.update(a.tobytes(order='C'))
    return h.hexdigest()


def dump(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def quantiles_or_sentinel(values: list[float], sentinel: float) -> tuple[float, float]:
    if not values:
        return float(sentinel), float(sentinel)
    x = np.asarray(values, dtype=np.float64)
    require(np.all(np.isfinite(x)), 'nonfinite confidence values')
    return float(np.median(x)), float(np.quantile(x, 0.90))


def instrumented_expand(
    *,
    families: list[dict[str, Any]],
    scan_by_year: dict[int, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[dict[str, float]]]]:
    """Exact v17 top-100 expansion plus observational confidence capture.

    Membership acceptance and winner ordering intentionally mirror
    v17.expand_top_ranked_memberships. The extra values stored in `accepted`
    never participate in a membership decision.
    """
    expanded = copy.deepcopy(families)
    lookup = {y: {str(e['id']): e for e in scan_by_year[y]} for y in YEARS}
    original = {str(f['family_id']): set(map(str, f['event_ids'])) for f in expanded}
    rank_by_id = {str(f['family_id']): int(f['rank']) for f in expanded}
    top_ids = {str(f['family_id']) for f in expanded if int(f['rank']) <= TOP_K}
    by_id = {str(f['family_id']): f for f in expanded}
    accepted: dict[str, list[dict[str, float]]] = defaultdict(list)
    diagnostics: dict[str, Any] = {
        'expand_top_k': TOP_K,
        'fixed_membership_source': 'pre-SonotaCo PR #461',
        'eligible_family_year_pairs': 0,
        'ineligible_family_year_pairs': 0,
        'new_members_by_year': {},
        'eligible_pairs_by_year': {},
        'conflicted_additions_by_year': {},
        'confidence_observational_only': True,
    }

    require(jc.ALPHA == 0.05, 'frozen conformal alpha changed')
    require(jc.DENSITY_CEILING == 1.5, 'frozen density ceiling changed')
    require(jc.TRAJECTORY_CEILING == 1.5, 'frozen trajectory ceiling changed')
    require(jc.ACTIVITY_PADDING_DEG == 6.0, 'frozen activity padding changed')

    for target_year in YEARS:
        source_year = YEARS[1] if target_year == YEARS[0] else YEARS[0]
        target = scan_by_year[target_year]
        target_sol = np.asarray([float(e['sol']) % 360.0 for e in target], dtype=np.float64)
        best: dict[str, tuple[tuple[float, float, int, str], str, float, float, float, float]] = {}
        eligible_pairs = 0

        for fid in sorted(top_ids, key=lambda x: (rank_by_id[x], x)):
            source_ids = sorted(original[fid] & set(lookup[source_year]))
            if len(source_ids) < 4:
                diagnostics['ineligible_family_year_pairs'] += 1
                continue
            diagnostics['eligible_family_year_pairs'] += 1
            source = [lookup[source_year][eid] for eid in source_ids]
            sd2 = jc.source_leave_one_out_d2(source)
            sr = jc.loo_residuals(source)
            source_scores = jc.fisher_nonconformity(
                jc.source_empirical_pvalues(sd2),
                jc.source_empirical_pvalues(sr),
            )
            model = jc.fit_trajectory(source)
            idx = np.flatnonzero(jc.in_activity_arc(target_sol, [float(e['sol']) for e in source]))
            candidates = [target[int(i)] for i in idx]
            d2 = jc.target_d2(candidates, source)
            residual = jc.trajectory_residuals(model, candidates)
            scores = jc.fisher_nonconformity(
                jc.target_empirical_pvalues(d2, sd2),
                jc.target_empirical_pvalues(residual, sr),
            )
            joint_p = jc.joint_conformal_pvalues(scores, source_scores)

            for i, d, r, s, p in zip(
                idx.tolist(), d2.tolist(), residual.tolist(), scores.tolist(), joint_p.tolist()
            ):
                eid = str(target[i]['id'])
                if eid in original[fid]:
                    continue
                if (
                    float(d) > jc.DENSITY_CEILING + 1e-12
                    or float(r) > jc.TRAJECTORY_CEILING + 1e-12
                    or float(p) <= jc.ALPHA + 1e-15
                ):
                    continue
                eligible_pairs += 1
                key = (-float(p), float(s), rank_by_id[fid], fid)
                old = best.get(eid)
                if old is None or key < old[0]:
                    best[eid] = (key, fid, float(d), float(r), float(s), float(p))

        additions: dict[str, list[str]] = defaultdict(list)
        for eid, (_key, fid, d, r, s, p) in best.items():
            additions[fid].append(eid)
            accepted[fid].append({
                'target_year': float(target_year),
                'd2': d,
                'trajectory_residual': r,
                'fisher_nonconformity': s,
                'joint_conformal_p': p,
            })
        for fid, ids in additions.items():
            by_id[fid]['event_ids'] = sorted(set(map(str, by_id[fid]['event_ids'])) | set(ids))

        diagnostics['new_members_by_year'][str(target_year)] = len(best)
        diagnostics['eligible_pairs_by_year'][str(target_year)] = eligible_pairs
        diagnostics['conflicted_additions_by_year'][str(target_year)] = max(0, eligible_pairs - len(best))

    diagnostics['total_new_members'] = sum(diagnostics['new_members_by_year'].values())
    diagnostics['expanded_membership_sha256'] = canonical_sha({
        str(f['family_id']): sorted(map(str, f['event_ids']))
        for f in expanded
        if int(f['rank']) <= TOP_K
    })

    for before, after in zip(families, expanded):
        require(
            str(before['family_id']) == str(after['family_id'])
            and int(before['rank']) == int(after['rank']),
            'rank/order changed during instrumented membership',
        )
        require(
            set(map(str, before['event_ids'])).issubset(set(map(str, after['event_ids']))),
            'original seed removed during instrumented membership',
        )
    return expanded, diagnostics, accepted


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--comparator', choices=['sugar', 'hdbscan'], required=True)
    p.add_argument('--rows-2013', type=Path, required=True)
    p.add_argument('--rows-2014', type=Path, required=True)
    p.add_argument('--support-source-parts', type=Path, required=True)
    p.add_argument('--candidate-payload', type=Path, required=True)
    p.add_argument('--baseline-payload', type=Path, required=True)
    p.add_argument('--scorer-parts', type=Path, required=True)
    p.add_argument('--ranker-source', type=Path, required=True)
    p.add_argument('--original-model', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.ranker_source) == EXPECTED_RANKER_SHA, '#839 ranker source changed')
    require(sha(a.original_model) == EXPECTED_MODEL_SHA, '#853 model changed')

    raw = {
        2013: json.loads(a.rows_2013.read_text()),
        2014: json.loads(a.rows_2014.read_text()),
    }
    forbidden = {'label', 'shower', 'truth', 'known_shower', 'native_background', 'sporadic'}
    for year in YEARS:
        require(raw[year] and all(int(x['year']) == year for x in raw[year]), f'invalid {year} rows')
        require(
            all(not (forbidden & {str(k).lower() for k in row}) for row in raw[year]),
            'truth-bearing field reached v27 pretruth stage',
        )
    canonical = v15_application.validate_pair(YEARS, raw)

    runtime, support, base, _ = load_support_base(
        p19_module=type('Shim', (), {'mult': v17.MULT})(),
        support_source_parts=a.support_source_parts,
        candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,
        scorer_parts=a.scorer_parts,
    )
    generators.configure_pair(
        YEARS,
        support=support,
        mult=v17.MULT,
        v6=v17.v6,
        v8=v17.v8,
        p19=p19,
        p20=p20,
    )
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, 'target firewall changed')
    support.CORPUS = p19.CORPUS

    hard = v17.build_hard_with_v15_order(
        scan_by_year=canonical,
        support=support,
        base=base,
        runtime=runtime,
    )
    soft19, _ = generators.build_p19_pair(
        years=YEARS,
        hard=hard,
        scan_by_year=canonical,
        support=support,
        base=base,
        p19=p19,
    )
    soft20 = generators.build_p20_pair(
        years=YEARS,
        hard=hard,
        scan_by_year=canonical,
        support=support,
        base=base,
        p20=p20,
    )['soft_families']
    families = hard['hard_families'] + soft19 + soft20
    sources = ['hard'] * len(hard['hard_families']) + ['p19'] * len(soft19) + ['p20'] * len(soft20)
    ids = [str(f['family_id']) for f in families]
    require(len(ids) == len(set(ids)), 'family IDs collide')
    source_by_id = {fid: src for fid, src in zip(ids, sources)}

    ranker = v22prep.load_module(a.ranker_source, 'frozen_839_v27_pretruth')
    xraw, centroids, tie = urc_application.build_feature_matrix(
        families=families,
        source_by_id=source_by_id,
        hard_order=hard['hard_order'],
        scan_by_year=canonical,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=ranker,
    )
    original = urc_application.score_and_rank(
        model_path=a.original_model,
        families=families,
        source_by_id=source_by_id,
        hard_order=hard['hard_order'],
        scan_by_year=canonical,
        years=YEARS,
        support=support,
        base=base,
        frozen_ranker_module=ranker,
    )
    quality_order = list(original['order'])
    consensus_order, consensus_diag = v19.raw_consensus_order(families, sources, support, base)
    v19_order = list(v19.fusion_orders(quality_order, consensus_order)['rank_sum'])

    xrel = v22prep.relative_noncat(xraw)
    graph = v22prep.consensus_graph_features(families, sources, support, base)
    priors = np.column_stack([
        v22prep.rank_percentile(quality_order, ids),
        v22prep.rank_percentile(consensus_order, ids),
        v22prep.rank_percentile(v19_order, ids),
    ])
    xbase = np.column_stack([xraw, xrel, priors, graph]).astype(np.float64, copy=False)
    centroid_array = np.asarray(centroids, dtype=np.float64)
    require(xbase.shape == (len(families), BASE_DIM), 'v27 base feature matrix shape changed')
    require(np.all(np.isfinite(xbase)), 'nonfinite base feature matrix')
    require(array_sha(xbase) == EXPECTED[a.comparator]['base_feature_sha256'], 'v22/v24 base feature identity failed')
    require(array_sha(centroid_array) == EXPECTED[a.comparator]['centroid_sha256'], 'v22/v24 centroid identity failed')

    by_id = {str(f['family_id']): f for f in families}
    ordered = []
    for rank, fid in enumerate(v19_order, start=1):
        f = by_id[fid]
        ordered.append({
            'family_id': fid,
            'rank': rank,
            'event_ids': sorted(set(map(str, f['event_ids']))),
            'source': source_by_id[fid],
        })

    expanded, membership_diag, accepted = instrumented_expand(
        families=ordered,
        scan_by_year=canonical,
    )
    require(canonical_sha(expanded) == EXPECTED[a.comparator]['expanded_family_sha256'], 'instrumented expansion changed frozen v19 memberships')

    top_ids = v19_order[:TOP_K]
    expanded_by = {str(f['family_id']): f for f in expanded}
    id_index = {fid: i for i, fid in enumerate(ids)}
    event_lookup = {
        str(row['id']): row
        for year in YEARS
        for row in canonical[year]
    }
    top_rows: list[dict[str, Any]] = []
    post_rows: list[list[float]] = []

    for fid in top_ids:
        core = by_id[fid]
        final_ids = sorted(set(map(str, expanded_by[fid]['event_ids'])))
        core_ids = set(map(str, core['event_ids']))
        added_ids = set(final_ids) - core_ids
        require(core_ids.issubset(set(final_ids)), f'core not preserved: {fid}')

        expanded_for_cohesion = copy.deepcopy(core)
        expanded_for_cohesion['event_ids'] = final_ids
        cohesion = urc_v2.cohesion_features(expanded_for_cohesion, event_lookup, support, base)
        require(len(cohesion) == 7, 'URC-v2 cohesion feature count changed')

        core_n = len(core_ids)
        add_n = len(added_ids)
        expansion = [
            math.log1p(core_n),
            math.log1p(add_n),
            float(add_n / max(core_n, 1)),
        ]

        conf = accepted.get(fid, [])
        d2 = [float(r['d2']) for r in conf]
        residual = [float(r['trajectory_residual']) for r in conf]
        neglogp = [-math.log(float(r['joint_conformal_p'])) for r in conf]
        d2_med, d2_q90 = quantiles_or_sentinel(d2, jc.DENSITY_CEILING)
        res_med, res_q90 = quantiles_or_sentinel(residual, jc.TRAJECTORY_CEILING)
        p_med, p_q90 = quantiles_or_sentinel(neglogp, -math.log(jc.ALPHA))
        confidence = [d2_med, d2_q90, res_med, res_q90, p_med, p_q90]

        row = [float(x) for x in (cohesion + expansion + confidence)]
        require(len(row) == POST_DIM and all(math.isfinite(x) for x in row), f'bad post-membership feature row: {fid}')
        post_rows.append(row)
        top_rows.append({
            'family_id': fid,
            'v19_rank': int(expanded_by[fid]['rank']),
            'source': str(expanded_by[fid].get('source')),
            'core_member_count': core_n,
            'added_member_count': add_n,
            'final_member_count': len(final_ids),
            'accepted_confidence_records': len(conf),
            'final_event_ids': final_ids,
        })

    xpost = np.asarray(post_rows, dtype=np.float64)
    top_indices = [id_index[fid] for fid in top_ids]
    xbase_top = xbase[top_indices]
    xcombined = np.column_stack([xbase_top, xpost]).astype(np.float64, copy=False)
    require(xpost.shape == (TOP_K, POST_DIM), 'post-membership feature matrix shape changed')
    require(xcombined.shape == (TOP_K, COMBINED_DIM), 'combined feature matrix shape changed')
    require(np.all(np.isfinite(xcombined)), 'nonfinite combined feature matrix')

    np.save(a.output / 'base_features_top100.npy', xbase_top, allow_pickle=False)
    np.save(a.output / 'post_membership_features_top100.npy', xpost, allow_pickle=False)
    np.save(a.output / 'combined_features_top100.npy', xcombined, allow_pickle=False)
    dump(a.output / 'expanded_top100_families.json', {
        'families': top_rows,
        'truth_accessed': False,
        'target_information_access': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    })

    manifest = {
        'verdict': 'PASS_V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE',
        'scientific_stage': 'V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE_ONLY',
        'comparator_route': a.comparator,
        'years': list(YEARS),
        'stage1_method': 'exact frozen v19 rank-sum',
        'stage1_family_count': len(families),
        'postmembership_rerank_scope': TOP_K,
        'stage1_top100_family_ids': top_ids,
        'base_feature_dimension': BASE_DIM,
        'post_membership_feature_dimension': POST_DIM,
        'combined_feature_dimension': COMBINED_DIM,
        'post_membership_feature_names': list(POST_FEATURE_NAMES),
        'post_membership_feature_provenance': {
            'cohesion_7': 'exact pre-SonotaCo URC-v2 cohesion feature definitions applied to expanded event IDs with original centroids',
            'expansion_3': 'pre-existing #846 feature forms: log1p core count, log1p addition count, addition/core ratio',
            'confidence_6': 'median/q90 summaries of accepted winning #461/v17 d2, trajectory residual, and -log(joint conformal p)',
            'no_addition_sentinels': {
                'd2': float(jc.DENSITY_CEILING),
                'trajectory_residual': float(jc.TRAJECTORY_CEILING),
                'neglog_joint_p': float(-math.log(jc.ALPHA)),
            },
        },
        'base_feature_sha256_full_universe': array_sha(xbase),
        'expected_base_feature_sha256_full_universe': EXPECTED[a.comparator]['base_feature_sha256'],
        'centroid_sha256_full_universe': array_sha(centroid_array),
        'expected_centroid_sha256_full_universe': EXPECTED[a.comparator]['centroid_sha256'],
        'expanded_family_sha256_full_universe': canonical_sha(expanded),
        'expected_expanded_family_sha256_full_universe': EXPECTED[a.comparator]['expanded_family_sha256'],
        'base_features_top100_sha256': array_sha(xbase_top),
        'post_membership_features_top100_sha256': array_sha(xpost),
        'combined_features_top100_sha256': array_sha(xcombined),
        'expanded_top100_family_payload_sha256': canonical_sha(top_rows),
        'membership_diagnostics': membership_diag,
        'consensus_diagnostics': consensus_diag,
        'successor_model_trained': False,
        'literature_evaluation_performed': False,
        'truth_accessed': False,
        'target_information_access': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    dump(a.output / 'V27_POSTMEMBERSHIP_FEATURE_MANIFEST.json', manifest)
    print(json.dumps({
        'verdict': manifest['verdict'],
        'comparator_route': a.comparator,
        'combined_feature_dimension': COMBINED_DIM,
        'combined_features_top100_sha256': manifest['combined_features_top100_sha256'],
        'expanded_family_identity_pass': True,
        'base_feature_identity_pass': True,
        'truth_accessed': False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
