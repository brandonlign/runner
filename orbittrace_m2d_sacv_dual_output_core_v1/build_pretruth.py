from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import orbittrace_m2d_sacv_fallback_recurrence_v1.build_pretruth as fr

SACV_V1_PRETRUTH_SHA256 = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
SACV_V1_ROLE = 'TARGET_EXCLUDED_SACV_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH'
ROLE = 'TARGET_EXCLUDED_SACV_PRIMARY_PLUS_NESTED_RECURRENT_CORE_FROZEN_BEFORE_SHOWER_TRUTH'
SCHEMA = 'ORBITTRACE_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH'


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def _subsets_by_key(payload: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(s['denominator']), int(s['bucket'])): s for s in payload['subsets']}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fair-pretruth', type=Path, required=True)
    ap.add_argument('--geometry', type=Path, required=True)
    ap.add_argument('--sacv-v1-pretruth', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(fr.sha(a.fair_pretruth) == fr.FAIR_SHA, 'fair pretruth changed')
    req(fr.sha(a.sacv_v1_pretruth) == SACV_V1_PRETRUTH_SHA256, 'SACV v1 oracle changed')
    fair = json.loads(a.fair_pretruth.read_text())
    geom = json.loads(a.geometry.read_text())
    oracle = json.loads(a.sacv_v1_pretruth.read_text())
    req(oracle['scientific_role'] == SACV_V1_ROLE, 'wrong SACV v1 oracle role')
    req(oracle['fair_pretruth_sha256'] == fr.FAIR_SHA, 'SACV v1 oracle parent changed')
    req(oracle['shower_truth_used'] is False and oracle['target_information_access'] is False and oracle['target_region_events_accessed'] is False, 'SACV v1 oracle firewall')

    req(geom['scientific_role'] == 'LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY', 'geometry role')
    req(int(geom['events_total']) == fr.EXPECTED_TOTAL and geom['events_by_year'] == fr.EXPECTED_COUNTS, 'geometry counts')
    req(geom['blind_exclusion'] == fr.BLIND and geom['shower_truth_exported'] is False, 'geometry firewall')
    events = list(geom['events'])
    req(len(events) == fr.EXPECTED_TOTAL, 'geometry rows')
    req(all(not (fr.BLIND[0] <= float(e['sol']) <= fr.BLIND[1]) for e in events), 'protected row survived')

    rt = fr.Runtime(events)
    req({str(y): len(rt.byyear[y]) for y in fr.YEARS} == fr.EXPECTED_COUNTS, 'runtime counts')
    oracle_subsets = _subsets_by_key(oracle)
    fair_subsets = _subsets_by_key(fair)
    req(set(oracle_subsets) == set(fair_subsets), 'oracle panel mismatch')

    subsets: list[dict[str, Any]] = []
    allrows: list[dict[str, Any]] = []
    oracle_equal = 0
    for s in fair['subsets']:
        d, b = int(s['denominator']), int(s['bucket'])
        parents = list(s['successor_candidates'])
        osub = oracle_subsets[(d, b)]
        orows = list(osub['extractions'])
        req(len(orows) == len(parents), f'oracle candidate count d{d}b{b}')
        req([int(x['internal_mass_rank']) for x in parents] == list(range(1, len(parents) + 1)), f'rank drift d{d}b{b}')
        rows = []
        for pos, (c, oref) in enumerate(zip(parents, orows), 1):
            raw = rt.proc(c, pos)
            parent_ids = sorted(map(str, c['event_ids']))
            req(int(raw['rank']) == pos == int(oref['rank']), f'rank mismatch d{d}b{b}/{pos}')
            req(str(raw['family_id']) == str(oref['family_id']) == str(c['family_id']), f'family mismatch d{d}b{b}/{pos}')
            req(str(raw['family_hash']) == str(oref['family_hash']) == str(c['family_hash']), f'hash mismatch d{d}b{b}/{pos}')

            route = str(raw['route'])
            recurrent_core_ids: list[str] = []
            selected_component = raw.get('selected_component')
            if route == 'recurrence_fallback':
                recurrent_core_ids = sorted(map(str, raw['output_ids']))
                primary_ids = parent_ids
                primary_refined = False
                dual_route = 'sacv_v1_parent_with_recurrent_core'
            elif route == 'sacv_v1_success':
                primary_ids = sorted(map(str, raw['output_ids']))
                primary_refined = len(primary_ids) < len(parent_ids)
                dual_route = 'sacv_v1_success'
                selected_component = None
            elif route == 'parent_fallback':
                primary_ids = parent_ids
                primary_refined = False
                dual_route = 'sacv_v1_parent_without_recurrent_core'
                selected_component = None
            else:
                raise RuntimeError(f'unknown frozen route {route}')

            oracle_ids = sorted(map(str, oref['output_ids']))
            req(primary_ids == oracle_ids, f'PRIMARY_SACV_V1_ID_MISMATCH d{d}b{b}/{pos}')
            req(bool(primary_refined) == bool(oref['refined']), f'PRIMARY_SACV_V1_REFINED_MISMATCH d{d}b{b}/{pos}')
            req(set(recurrent_core_ids).issubset(set(parent_ids)), f'core escaped parent d{d}b{b}/{pos}')
            req(not recurrent_core_ids or primary_ids == parent_ids, f'core emitted outside SACV fallback d{d}b{b}/{pos}')
            oracle_equal += 1

            row = {
                'rank': pos,
                'family_id': str(c['family_id']),
                'family_hash': str(c['family_hash']),
                'parent_n': len(parent_ids),
                'refined': bool(primary_refined),
                'output_n': len(primary_ids),
                'ratio': len(primary_ids) / len(parent_ids) if parent_ids else 0.0,
                'output_ids': primary_ids,
                'route': dual_route,
                'original_sacv_validated': bool(raw['original_sacv_validated']),
                'recurrent_core_ids': recurrent_core_ids,
                'recurrent_core_n': len(recurrent_core_ids),
                'core_refined': bool(recurrent_core_ids and len(recurrent_core_ids) < len(primary_ids)),
                'core_ratio_to_primary': (len(recurrent_core_ids) / len(primary_ids)) if primary_ids else 0.0,
                'annual_admissible_counts': raw['annual_admissible_counts'],
                'annual_top_ids': raw['annual_top_ids'],
                'recurrent_component_count': int(raw['recurrent_component_count']),
                'selected_recurrent_core_component': selected_component,
                'all_component_summaries': raw['all_component_summaries'],
            }
            rows.append(row)
            allrows.append(row)
        subsets.append({'denominator': d, 'bucket': b, 'parent_candidate_count': len(parents), 'extractions': rows})
        core_rows = [x for x in rows if x['recurrent_core_n'] > 0]
        print(json.dumps({
            'panel': f'd{d}_b{b}',
            'candidates': len(rows),
            'primary_refined': sum(x['refined'] for x in rows),
            'nested_cores': len(core_rows),
            'mean_primary_ratio': float(np.mean([x['ratio'] for x in rows])) if rows else 0.0,
            'mean_core_ratio': float(np.mean([x['core_ratio_to_primary'] for x in core_rows])) if core_rows else 0.0,
        }, sort_keys=True), flush=True)

    req(oracle_equal == int(oracle['summary']['candidate_occurrences']) == len(allrows) == 328, 'primary oracle equality count')
    core_rows = [x for x in allrows if x['recurrent_core_n'] > 0]
    payload = {
        'schema': SCHEMA,
        'scientific_role': ROLE,
        'fair_pretruth_sha256': fr.FAIR_SHA,
        'geometry_sha256': fr.sha(a.geometry),
        'sacv_v1_pretruth_sha256': SACV_V1_PRETRUTH_SHA256,
        'years': list(fr.YEARS),
        'blind_exclusion': fr.BLIND,
        'configuration': {
            'rmax': fr.RMAX,
            'minimum_support': fr.MIN_SUPPORT,
            'contamination_max': fr.CONTAM_MAX,
            'analog_offsets_deg': fr.DELTAS[1:].tolist(),
            'physical_scales': {'solar_deg': 5.0, 'radiant_deg': 4.0, 'speed_fraction': 0.10},
            'primary': 'exact_frozen_sacv_v1_output_ids_and_rank',
            'nested_core_trigger': 'only_when_exact_sacv_v1_top1_pair_fails_and_frozen_recurrent_component_exists',
            'nested_core_component_selector': ['edge_count_desc', 'node_count_desc', 'min_cross_support_desc', 'member_n_asc', 'membership_hash_asc'],
            'nested_core_membership': 'natural_union_of_all_local_hypothesis_memberships_in_frozen_selected_component',
            'core_is_second_ranked_candidate': False,
        },
        'subsets': subsets,
        'summary': {
            'candidate_occurrences': len(allrows),
            'primary_oracle_exact_id_equal_occurrences': oracle_equal,
            'primary_refined_occurrences': sum(x['refined'] for x in allrows),
            'nested_core_occurrences': len(core_rows),
            'nested_core_strict_refinements': sum(x['core_refined'] for x in core_rows),
            'mean_parent_n': float(np.mean([x['parent_n'] for x in allrows])),
            'mean_primary_n': float(np.mean([x['output_n'] for x in allrows])),
            'mean_nested_core_n': float(np.mean([x['recurrent_core_n'] for x in core_rows])) if core_rows else 0.0,
            'mean_nested_core_ratio_to_primary': float(np.mean([x['core_ratio_to_primary'] for x in core_rows])) if core_rows else 0.0,
        },
        'primary_output_exact_sacv_v1': True,
        'primary_discovery_membership_changed': False,
        'primary_discovery_rank_changed': False,
        'parent_rank_changed': False,
        'nested_core_changes_primary_matching': False,
        'shower_truth_used': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'sonotaco_scientific_access': False,
        'post_result_parameter_search': False,
        'post_target_reveal_development': True,
    }
    a.output.write_text(json.dumps(payload, separators=(',', ':'), sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': 'PASS_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH', 'sha256': fr.sha(a.output), 'summary': payload['summary']}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
