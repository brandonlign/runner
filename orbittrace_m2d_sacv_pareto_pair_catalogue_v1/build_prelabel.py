#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import orbittrace_m2d_sacv_pair_v2.build_pretruth as pv

FAIR_SHA = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
SACV_V1_PRETRUTH_SHA = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
GEOMETRY_SHA = '1fd5cd0577d88784845e0d367ef35491d6afb7caa78bb06fa05d72048daec384'
EXPECTED_TOTAL = 738682
EXPECTED_COUNTS = {'2022': 315024, '2023': 423658}
BLIND = [20.0, 55.0]
YEARS = (2022, 2023)


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pair_hash(family_hash: str, a: str, b: str) -> str:
    return hashlib.sha256(f'{family_hash}|{a}|{b}'.encode()).hexdigest()


def annual_order(hs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Exact original #1405 SACV-v1 select_source key, expressed as an
    # ascending Python sort: maximize (excess, support, -contamination, -radius),
    # then choose the lexicographically smaller center ID.
    return sorted(
        hs,
        key=lambda h: (
            -float(h['excess']),
            -int(h['parent_support']),
            float(h['contamination']),
            float(h['radius']),
            str(h['id']),
        ),
    )


class Fenwick2DMax:
    def __init__(self, na: int, nb: int) -> None:
        self.na = na
        self.nb = nb
        self.t = [[0] * (nb + 2) for _ in range(na + 2)]

    def query(self, a: int, b: int) -> int:
        ans = 0
        i = a
        while i > 0:
            j = b
            row = self.t[i]
            while j > 0:
                ans = max(ans, row[j])
                j -= j & -j
            i -= i & -i
        return ans

    def update(self, a: int, b: int, value: int) -> None:
        i = a
        while i <= self.na:
            j = b
            row = self.t[i]
            while j <= self.nb:
                if value > row[j]:
                    row[j] = value
                j += j & -j
            i += i & -i


def assign_pareto_layers(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    max_a = max(int(r['annual_rank_2022']) for r in rows)
    max_b = max(int(r['annual_rank_2023']) for r in rows)
    fw = Fenwick2DMax(max_a, max_b)
    # Parent ranks are unique per parent. Within one parent every validated
    # endpoint-rank pair is unique, so sequential updates implement exact
    # 3-D dominance depth for (P,A,B).
    for r in sorted(
        rows,
        key=lambda z: (
            int(z['parent_rank']),
            int(z['annual_rank_2022']),
            int(z['annual_rank_2023']),
            str(z['pair_hash']),
        ),
    ):
        a = int(r['annual_rank_2022'])
        b = int(r['annual_rank_2023'])
        layer = 1 + fw.query(a, b)
        r['pareto_layer'] = layer
        fw.update(a, b, layer)

    rows.sort(key=lambda z: (int(z['pareto_layer']), str(z['pair_hash'])))
    for i, r in enumerate(rows, 1):
        r['rank'] = i


def _subsets(payload: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(s['denominator']), int(s['bucket'])): s for s in payload['subsets']}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fair-pretruth', type=Path, required=True)
    ap.add_argument('--geometry', type=Path, required=True)
    ap.add_argument('--sacv-v1-pretruth', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.fair_pretruth) == FAIR_SHA, 'fair pretruth changed')
    req(sha(a.geometry) == GEOMETRY_SHA, 'label-free geometry changed')
    req(sha(a.sacv_v1_pretruth) == SACV_V1_PRETRUTH_SHA, 'SACV-v1 pretruth changed')
    fair = json.loads(a.fair_pretruth.read_text())
    geom = json.loads(a.geometry.read_text())
    sacv = json.loads(a.sacv_v1_pretruth.read_text())

    req(fair['shower_truth_used'] is False, 'fair truth firewall')
    req(fair['target_information_access'] is False and fair['target_region_events_accessed'] is False, 'fair target firewall')
    req(geom['scientific_role'] == 'LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY', 'geometry role')
    req(int(geom['events_total']) == EXPECTED_TOTAL and geom['events_by_year'] == EXPECTED_COUNTS, 'geometry counts')
    req(geom['blind_exclusion'] == BLIND and geom['shower_truth_exported'] is False, 'geometry firewall')
    req(sacv['scientific_role'] == 'TARGET_EXCLUDED_SACV_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH', 'SACV-v1 role')
    req(sacv['shower_truth_used'] is False and sacv['target_information_access'] is False and sacv['target_region_events_accessed'] is False, 'SACV-v1 firewall')

    events = list(geom['events'])
    req(len(events) == EXPECTED_TOTAL, 'geometry row count')
    req(all(not (BLIND[0] <= float(e['sol']) <= BLIND[1]) for e in events), 'protected event survived')
    rt = pv.Runtime(events)
    req({str(y): len(rt.byyear[y]) for y in YEARS} == EXPECTED_COUNTS, 'runtime annual counts')

    sacv_sub = _subsets(sacv)
    req(set(sacv_sub) == {(int(s['denominator']), int(s['bucket'])) for s in fair['subsets']}, 'SACV/fair panel mismatch')

    panels: list[dict[str, Any]] = []
    capacity_ok = True
    total_pairs = 0
    all_year_support_ok = True
    for fs in fair['subsets']:
        d, b = int(fs['denominator']), int(fs['bucket'])
        parents = list(fs['successor_candidates'])
        K = len(parents)
        req([int(x['internal_mass_rank']) for x in parents] == list(range(1, K + 1)), f'parent rank drift d{d}b{b}')
        annual_ids = {str(y): list(fs['annual_event_ids'][str(y)]) for y in YEARS}
        req(len(annual_ids['2022']) + len(annual_ids['2023']) == int(fs['event_count']), f'panel universe count d{d}b{b}')

        sv = sacv_sub[(d, b)]
        srows = list(sv['extractions'])
        req(len(srows) == K, f'SACV-v1 capacity drift d{d}b{b}')
        baseline = []
        children: list[dict[str, Any]] = []
        annual_rank_audits = []

        for pos, (c, sr) in enumerate(zip(parents, srows), 1):
            parent_ids = sorted(map(str, c['event_ids']))
            req(int(sr['rank']) == pos, f'SACV-v1 rank mismatch d{d}b{b}/{pos}')
            req(str(sr['family_hash']) == str(c['family_hash']), f'SACV-v1 family mismatch d{d}b{b}/{pos}')
            baseline.append({
                'rank': pos,
                'family_id': str(sr['family_id']),
                'family_hash': str(sr['family_hash']),
                'event_ids': sorted(map(str, sr['output_ids'])),
                'catalogue_source': 'exact_sacv_v1',
            })

            src = {2022: rt.enumerate_sources(parent_ids, 2022), 2023: rt.enumerate_sources(parent_ids, 2023)}
            rankmaps: dict[int, dict[str, int]] = {}
            for y in YEARS:
                ordered = annual_order(src[y])
                rankmaps[y] = {str(h['id']): i for i, h in enumerate(ordered, 1)}
                req(sorted(rankmaps[y].values()) == list(range(1, len(src[y]) + 1)), f'annual rank permutation d{d}b{b}/{pos}/{y}')
                # Store only compact zero-label audit metadata, not centers.
                annual_rank_audits.append({
                    'parent_rank': pos,
                    'year': y,
                    'hypothesis_count': len(src[y]),
                    'ordered_center_ids': [str(h['id']) for h in ordered],
                })
                other = 2023 if y == 2022 else 2022
                for h in src[y]:
                    h['members_all'] = rt.members(parent_ids, h['center'], h['radius'])
                    h['cross_support'] = sum(rt.byid[eid]['year'] == other for eid in h['members_all'])

            for ha in src[2022]:
                if int(ha['cross_support']) < pv.MIN_SUPPORT:
                    continue
                for hb in src[2023]:
                    if int(hb['cross_support']) < pv.MIN_SUPPORT:
                        continue
                    dist = float(__import__('numpy').linalg.norm(ha['center'] - hb['center']))
                    if dist > float(ha['radius']) + 1e-12 or dist > float(hb['radius']) + 1e-12:
                        continue
                    member_ids = sorted(set(ha['members_all']) | set(hb['members_all']))
                    n22 = sum(rt.byid[eid]['year'] == 2022 for eid in member_ids)
                    n23 = sum(rt.byid[eid]['year'] == 2023 for eid in member_ids)
                    all_year_support_ok = all_year_support_ok and n22 >= 4 and n23 >= 4
                    children.append({
                        'parent_rank': pos,
                        'parent_family_id': str(c['family_id']),
                        'parent_family_hash': str(c['family_hash']),
                        'annual_rank_2022': int(rankmaps[2022][str(ha['id'])]),
                        'annual_rank_2023': int(rankmaps[2023][str(hb['id'])]),
                        'center_id_2022': str(ha['id']),
                        'center_id_2023': str(hb['id']),
                        'pair_hash': pair_hash(str(c['family_hash']), str(ha['id']), str(hb['id'])),
                        'event_ids': member_ids,
                        'member_n': len(member_ids),
                        'member_n_2022': n22,
                        'member_n_2023': n23,
                        'endpoint_2022': {
                            'excess': float(ha['excess']), 'parent_support': int(ha['parent_support']),
                            'contamination': float(ha['contamination']), 'radius': float(ha['radius']),
                        },
                        'endpoint_2023': {
                            'excess': float(hb['excess']), 'parent_support': int(hb['parent_support']),
                            'contamination': float(hb['contamination']), 'radius': float(hb['radius']),
                        },
                        'catalogue_source': 'm2d_sacv_validated_pair',
                    })

        req(len({r['pair_hash'] for r in children}) == len(children), f'pair identity collision d{d}b{b}')
        assign_pareto_layers(children)
        req([int(x['rank']) for x in children] == list(range(1, len(children) + 1)), f'catalogue rank permutation d{d}b{b}')
        panel_capacity = len(children) >= K
        capacity_ok = capacity_ok and panel_capacity
        total_pairs += len(children)
        panels.append({
            'denominator': d,
            'bucket': b,
            'event_count': int(fs['event_count']),
            'annual_event_ids': annual_ids,
            'equal_budget_k': K,
            'complete_pair_candidate_count': len(children),
            'capacity_ok': panel_capacity,
            'sacv_v1_candidates': baseline,
            'successor_candidates': children,
            'annual_rank_audits': annual_rank_audits,
        })
        print(json.dumps({'panel': f'd{d}_b{b}', 'K': K, 'pairs': len(children), 'max_layer': max([int(x['pareto_layer']) for x in children], default=0), 'capacity_ok': panel_capacity}, sort_keys=True), flush=True)

    prelabel = {
        'schema': 'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL',
        'scientific_role': 'TARGET_EXCLUDED_COMPLETE_SACV_VALIDATED_PAIR_CATALOGUE_FROZEN_BEFORE_SHOWER_TRUTH',
        'fair_pretruth_sha256': FAIR_SHA,
        'geometry_sha256': GEOMETRY_SHA,
        'sacv_v1_pretruth_sha256': SACV_V1_PRETRUTH_SHA,
        'configuration': {
            'annual_hypothesis_order': 'excess_desc_parent_support_desc_contamination_asc_radius_asc_center_id_asc',
            'pair_validation': 'exact_sacv_v1_reciprocal_crossyear_validation',
            'pair_membership': 'exact_union_of_endpoint_sacv_balls_within_immutable_parent',
            'pareto_objectives_minimized': ['immutable_m2d_parent_rank', 'sacv_2022_hypothesis_rank', 'sacv_2023_hypothesis_rank'],
            'pareto': 'ordinary_nondominated_layers',
            'final_order': 'pareto_layer_asc_pair_hash_asc',
            'pair_hash': 'sha256(parent_family_hash|center_2022_id|center_2023_id)',
            'duplicate_membership_policy': 'retain_distinct_pair_identities_and_consume_budget',
            'equal_budget': 'exact_sacv_v1_parent_candidate_count_per_panel',
            'fallback_fill': 'forbidden',
        },
        'years': list(YEARS),
        'blind_exclusion': BLIND,
        'panels': panels,
        'summary': {'panels': len(panels), 'validated_pair_candidates': total_pairs, 'all_panel_capacity_ok': capacity_ok, 'all_pair_year_support_ok': all_year_support_ok},
        'shower_truth_used': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'sonotaco_scientific_access': False,
        'post_result_parameter_search': False,
        'post_target_reveal_development': True,
    }
    pre_path = a.output / 'M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL.json'
    pre_path.write_text(json.dumps(prelabel, separators=(',', ':'), sort_keys=True, allow_nan=False) + '\n')

    gates = {
        'fair_and_geometry_frozen': True,
        'firewall_clean': True,
        'all_pairs_exact_validated_children': True,
        'all_memberships_exact_endpoint_unions': True,
        'annual_hypothesis_rank_permutations_valid': True,
        'pareto_layers_valid_by_exact_prefix_depth': True,
        'catalogue_rank_permutations_valid': True,
        'all_pairs_have_minimum_annual_support': all_year_support_ok,
        'all_panels_have_equal_budget_capacity': capacity_ok,
        'truth_and_external_data_inaccessible': True,
    }
    verdict = 'PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH' if all(gates.values()) else 'POWER_INCONCLUSIVE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT'
    audit = {
        'schema': 'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH',
        'scientific_role': 'ZERO_LABEL_PRETRUTH_AUTHORIZATION',
        'verdict': verdict,
        'prelabel_sha256': sha(pre_path),
        'gates': gates,
        'summary': prelabel['summary'],
        'shower_truth_used': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'sonotaco_scientific_access': False,
    }
    audit_path = a.output / 'M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH.json'
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': verdict, 'prelabel_sha256': audit['prelabel_sha256'], 'summary': audit['summary']}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
