from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato

import orbittrace_m2d_sacv_fallback_recurrence_v1.build_pretruth as fr

SACV_V1_PRETRUTH_SHA256 = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
SACV_V1_ROLE = 'TARGET_EXCLUDED_SACV_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH'
ROLE = 'TARGET_EXCLUDED_SACV_PRIMARY_PLUS_TOPOMODAL_TRUNK_RECURRENT_CORE_FROZEN_BEFORE_SHOWER_TRUTH'
SCHEMA = 'ORBITTRACE_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_PRETRUTH'
MIN_ANNUAL_SUPPORT = 4


def req(x: bool, msg: str) -> None:
    if not x:
        raise RuntimeError(msg)


def membership_sha(ids: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256('|'.join(sorted(map(str, ids))).encode()).hexdigest()


def _subsets_by_key(payload: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(s['denominator']), int(s['bucket'])): s for s in payload['subsets']}


def topomodal_trunk_core(
    graph_nodes: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
    event_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    node_ids = sorted(str(n['node_id']) for n in graph_nodes)
    req(len(node_ids) >= 2 and len(node_ids) == len(set(node_ids)), 'invalid selected graph nodes')
    row_by_node = {str(n['node_id']): n for n in graph_nodes}
    req(set(row_by_node) == set(node_ids), 'selected graph node identity mismatch')

    pos = {n: i for i, n in enumerate(node_ids)}
    adjacency = [set([i]) for i in range(len(node_ids))]
    exact_edges: set[tuple[str, str]] = set()
    for e in graph_edges:
        u, v = str(e['u']), str(e['v'])
        req(u in pos and v in pos and u != v, 'selected edge escaped graph')
        a, b = sorted((u, v))
        req((a, b) not in exact_edges, 'duplicate selected edge')
        exact_edges.add((a, b))
        adjacency[pos[u]].add(pos[v])
        adjacency[pos[v]].add(pos[u])
    req(exact_edges, 'selected recurrence component has no edge')
    req(all(len(a) >= 2 for a in adjacency), 'selected recurrence node has no validated neighbor')

    # The selected component must be connected under the exact validated edges.
    seen = {0}
    stack = [0]
    while stack:
        i = stack.pop()
        for j in adjacency[i]:
            if j not in seen:
                seen.add(j)
                stack.append(j)
    req(len(seen) == len(node_ids), 'selected recurrence graph disconnected')

    neighbors = [sorted(a) for a in adjacency]
    rho = np.asarray([len(a) / float(len(node_ids)) for a in neighbors], dtype=float)
    req(np.all(np.isfinite(rho)) and np.all(rho > 0.0), 'invalid hypothesis graph density')

    model = Tomato(graph_type='manual', density_type='manual')
    model.fit(neighbors, weights=rho)
    leaf_labels = np.asarray(model.leaf_labels_, dtype=np.int64)
    req(leaf_labels.shape == (len(node_ids),), 'wrong ToMATo hypothesis leaf labels')
    leaf_count = int(model.n_leaves_)
    req(leaf_count >= 1, 'no ToMATo hypothesis leaves')
    req(int(leaf_labels.min()) >= 0 and int(leaf_labels.max()) + 1 == leaf_count, 'noncontiguous hypothesis leaves')
    children = np.asarray(model.children_, dtype=np.int64).reshape((-1, 2))
    roots_expected = len(np.asarray(model.max_weight_per_cc_, dtype=float))
    req(roots_expected == 1, 'selected recurrence component did not produce one ToMATo root')
    req(leaf_count - len(children) == roots_expected, 'hypothesis hierarchy arithmetic changed')

    node_count = leaf_count + len(children)
    member_ix: list[frozenset[int] | None] = [None] * node_count
    for leaf in range(leaf_count):
        ix = np.flatnonzero(leaf_labels == leaf)
        req(len(ix) > 0, f'empty hypothesis leaf {leaf}')
        member_ix[leaf] = frozenset(int(i) for i in ix)
    req(sum(len(member_ix[i]) for i in range(leaf_count) if member_ix[i] is not None) == len(node_ids), 'hypothesis leaves do not partition graph')

    parent = np.full(node_count, -1, dtype=np.int64)
    for offset, pair in enumerate(children):
        hnode = leaf_count + offset
        a, b = int(pair[0]), int(pair[1])
        req(0 <= a < hnode and 0 <= b < hnode and a != b, 'invalid hypothesis hierarchy children')
        req(parent[a] == -1 and parent[b] == -1, 'hypothesis hierarchy multiple parents')
        ma, mb = member_ix[a], member_ix[b]
        req(ma is not None and mb is not None and ma.isdisjoint(mb), 'invalid hypothesis hierarchy membership')
        member_ix[hnode] = frozenset(ma.union(mb))
        parent[a] = hnode
        parent[b] = hnode
    roots = np.flatnonzero(parent == -1)
    req(len(roots) == 1 and len(member_ix[int(roots[0])]) == len(node_ids), 'hypothesis root mismatch')

    max_rho = float(np.max(rho))
    anchor_candidates = [i for i, x in enumerate(rho) if float(x) == max_rho]
    anchor_ix = min(anchor_candidates, key=lambda i: node_ids[i])
    anchor_node_id = node_ids[anchor_ix]
    hnode = int(leaf_labels[anchor_ix])
    chain_nodes: list[int] = []
    seen_h: set[int] = set()
    while True:
        req(hnode not in seen_h, 'cycle in hypothesis hierarchy')
        seen_h.add(hnode)
        chain_nodes.append(hnode)
        par = int(parent[hnode])
        if par == -1:
            break
        hnode = par

    def event_union(hypothesis_ids: tuple[str, ...]) -> tuple[str, ...]:
        mids: set[str] = set()
        for n in hypothesis_ids:
            mids.update(map(str, row_by_node[n]['members']))
        return tuple(sorted(mids))

    full_hypothesis_ids = tuple(node_ids)
    full_event_ids = event_union(full_hypothesis_ids)
    req(full_event_ids, 'selected component has empty event union')
    full_event_set = frozenset(full_event_ids)

    chain_rows: list[dict[str, Any]] = []
    reportable: list[tuple[int, tuple[str, ...], tuple[str, ...]]] = []
    seen_hypothesis_memberships: set[tuple[str, ...]] = set()
    for chain_index, hn in enumerate(chain_nodes):
        ixset = member_ix[hn]
        req(ixset is not None, 'missing anchor-chain hypothesis membership')
        hypothesis_ids = tuple(sorted(node_ids[i] for i in ixset))
        if hypothesis_ids in seen_hypothesis_memberships:
            continue
        seen_hypothesis_memberships.add(hypothesis_ids)
        event_ids = event_union(hypothesis_ids)
        annual = {str(y): 0 for y in fr.YEARS}
        for eid in event_ids:
            req(eid in event_by_id, 'hypothesis event outside geometry')
            annual[str(int(event_by_id[eid]['year']))] += 1
        strict_hypothesis = hypothesis_ids != full_hypothesis_ids
        strict_event = frozenset(event_ids) != full_event_set
        recurrently_reportable = bool(
            strict_hypothesis
            and strict_event
            and all(annual[str(y)] >= MIN_ANNUAL_SUPPORT for y in fr.YEARS)
        )
        row = {
            'chain_index': int(chain_index),
            'hierarchy_node_id': int(hn),
            'hypothesis_node_count': len(hypothesis_ids),
            'hypothesis_node_ids': list(hypothesis_ids),
            'hypothesis_membership_sha256': membership_sha(hypothesis_ids),
            'event_member_count': len(event_ids),
            'event_ids': list(event_ids),
            'event_membership_sha256': membership_sha(event_ids),
            'events_by_year': annual,
            'strict_hypothesis_subset': strict_hypothesis,
            'strict_event_subset_of_component_union': strict_event,
            'recurrently_reportable': recurrently_reportable,
        }
        chain_rows.append(row)
        if recurrently_reportable:
            reportable.append((len(hypothesis_ids), hypothesis_ids, event_ids))

    if reportable:
        best_n = max(x[0] for x in reportable)
        best = [(hids, eids) for n, hids, eids in reportable if n == best_n]
        req(all(x == best[0] for x in best), 'nonunique equal-size hypothesis trunk')
        selected_hypotheses, core_ids = best[0]
        decision = 'TOPOMODAL_TRUNK_CORE'
    else:
        selected_hypotheses, core_ids = tuple(), tuple()
        decision = 'NO_REPORTABLE_STRICT_TOPOMODAL_TRUNK'

    if core_ids:
        req(frozenset(core_ids) < full_event_set, 'TopoModal trunk did not strictly refine natural component union')
    summary = {
        'selected_component_hypothesis_nodes': len(node_ids),
        'selected_component_validated_edges': len(exact_edges),
        'selected_component_event_union_n': len(full_event_ids),
        'selected_component_event_union_sha256': membership_sha(full_event_ids),
        'manual_graph_self_included': True,
        'density': '(validated_degree_plus_self)/component_node_count',
        'leaf_count': leaf_count,
        'internal_node_count': len(children),
        'root_count': 1,
        'anchor_hypothesis_node_id': anchor_node_id,
        'anchor_density': max_rho,
        'anchor_leaf_node': int(leaf_labels[anchor_ix]),
        'anchor_root_node': int(chain_nodes[-1]),
        'anchor_chain_unique_membership_count': len(chain_rows),
        'anchor_chain': chain_rows,
        'decision': decision,
        'selected_trunk_hypothesis_node_ids': list(selected_hypotheses),
        'selected_trunk_hypothesis_node_count': len(selected_hypotheses),
        'core_event_n': len(core_ids),
        'core_event_sha256': membership_sha(core_ids) if core_ids else None,
    }
    return list(core_ids), summary


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
    event_by_id = {str(e['id']): e for e in events}
    req(len(event_by_id) == len(events), 'duplicate geometry IDs')

    rt = fr.Runtime(events)
    req({str(y): len(rt.byyear[y]) for y in fr.YEARS} == fr.EXPECTED_COUNTS, 'runtime counts')
    oracle_subsets = _subsets_by_key(oracle)
    fair_subsets = _subsets_by_key(fair)
    req(set(oracle_subsets) == set(fair_subsets), 'oracle panel mismatch')

    subsets: list[dict[str, Any]] = []
    allrows: list[dict[str, Any]] = []
    oracle_equal = 0
    recurrence_fallbacks = 0
    for s in fair['subsets']:
        d, b = int(s['denominator']), int(s['bucket'])
        parents = list(s['successor_candidates'])
        orows = list(oracle_subsets[(d, b)]['extractions'])
        req(len(orows) == len(parents), f'oracle candidate count d{d}b{b}')
        rows = []
        for pos, (c, oref) in enumerate(zip(parents, orows), 1):
            raw = rt.proc(c, pos)
            parent_ids = sorted(map(str, c['event_ids']))
            req(int(raw['rank']) == pos == int(oref['rank']), f'rank mismatch d{d}b{b}/{pos}')
            req(str(raw['family_id']) == str(oref['family_id']) == str(c['family_id']), f'family mismatch d{d}b{b}/{pos}')
            req(str(raw['family_hash']) == str(oref['family_hash']) == str(c['family_hash']), f'hash mismatch d{d}b{b}/{pos}')

            route = str(raw['route'])
            if route == 'sacv_v1_success':
                primary_ids = sorted(map(str, raw['output_ids']))
                primary_refined = len(primary_ids) < len(parent_ids)
                core_ids: list[str] = []
                topo = None
                dual_route = 'sacv_v1_success'
            elif route == 'recurrence_fallback':
                recurrence_fallbacks += 1
                primary_ids = parent_ids
                primary_refined = False
                graph_nodes = list(raw.get('selected_graph_nodes') or [])
                graph_edges = list(raw.get('selected_graph_edges') or [])
                req(graph_nodes and graph_edges, f'missing instrumented recurrence graph d{d}b{b}/{pos}')
                core_ids, topo = topomodal_trunk_core(graph_nodes, graph_edges, event_by_id)
                dual_route = 'sacv_v1_parent_with_recurrent_core' if core_ids else 'sacv_v1_parent_no_reportable_topomodal_trunk'
            elif route == 'parent_fallback':
                primary_ids = parent_ids
                primary_refined = False
                core_ids = []
                topo = None
                dual_route = 'sacv_v1_parent_without_recurrence_component'
            else:
                raise RuntimeError(f'unknown frozen route {route}')

            oracle_ids = sorted(map(str, oref['output_ids']))
            req(primary_ids == oracle_ids, f'PRIMARY_SACV_V1_ID_MISMATCH d{d}b{b}/{pos}')
            req(bool(primary_refined) == bool(oref['refined']), f'PRIMARY_SACV_V1_REFINED_MISMATCH d{d}b{b}/{pos}')
            req(set(core_ids).issubset(set(parent_ids)), f'core escaped parent d{d}b{b}/{pos}')
            req(not core_ids or primary_ids == parent_ids, f'core emitted outside SACV fallback d{d}b{b}/{pos}')
            if core_ids:
                req(route == 'recurrence_fallback', f'core route contamination d{d}b{b}/{pos}')
                req(len(core_ids) < int(topo['selected_component_event_union_n']), f'core not strict vs natural union d{d}b{b}/{pos}')
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
                'topomodal_trunk_core_ids': core_ids,
                'topomodal_trunk_core_n': len(core_ids),
                'recurrent_core_ids': core_ids,
                'recurrent_core_n': len(core_ids),
                'core_refined': bool(core_ids and len(core_ids) < len(primary_ids)),
                'core_ratio_to_primary': (len(core_ids) / len(primary_ids)) if primary_ids else 0.0,
                'annual_admissible_counts': raw['annual_admissible_counts'],
                'annual_top_ids': raw['annual_top_ids'],
                'recurrent_component_count': int(raw['recurrent_component_count']),
                'selected_recurrent_component': raw.get('selected_component'),
                'all_component_summaries': raw['all_component_summaries'],
                'topomodal_trunk': topo,
            }
            rows.append(row)
            allrows.append(row)
        subsets.append({'denominator': d, 'bucket': b, 'parent_candidate_count': len(parents), 'extractions': rows})
        core_rows = [x for x in rows if x['topomodal_trunk_core_n'] > 0]
        print(json.dumps({
            'panel': f'd{d}_b{b}',
            'candidates': len(rows),
            'primary_refined': sum(x['refined'] for x in rows),
            'recurrence_fallbacks': sum(x['topomodal_trunk'] is not None for x in rows),
            'topomodal_trunk_cores': len(core_rows),
            'mean_core_ratio': float(np.mean([x['core_ratio_to_primary'] for x in core_rows])) if core_rows else 0.0,
        }, sort_keys=True), flush=True)

    req(oracle_equal == int(oracle['summary']['candidate_occurrences']) == len(allrows) == 328, 'primary oracle equality count')
    core_rows = [x for x in allrows if x['topomodal_trunk_core_n'] > 0]
    topo_rows = [x for x in allrows if x['topomodal_trunk'] is not None]
    req(len(topo_rows) == recurrence_fallbacks, 'recurrence fallback accounting')
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
            'nested_core_trigger': 'only_exact_recurrence_fallback_route',
            'recurrence_component_selector': ['edge_count_desc', 'node_count_desc', 'min_cross_support_desc', 'member_n_asc', 'membership_hash_asc'],
            'topology_graph': 'exact_selected_validated_recurrence_component_edges_plus_self_neighborhood',
            'topology_density': '(validated_degree_plus_self)/component_node_count',
            'topology_engine': 'gudhi_3.12.0_Tomato_manual_graph_manual_density_no_persistence_cut',
            'anchor': 'max_density_then_lexicographic_node_id',
            'trunk': 'largest_hypothesis_node_count_reportable_strict_state_on_anchor_chain',
            'reportability': 'strict_hypothesis_subset_and_strict_event_subset_and_event_support_4_per_year',
            'nested_core_membership': 'event_union_of_frozen_local_hypothesis_memberships_in_selected_trunk_state',
            'no_reportable_trunk_fallback': 'no_nested_core',
            'core_is_second_ranked_candidate': False,
        },
        'subsets': subsets,
        'summary': {
            'candidate_occurrences': len(allrows),
            'primary_oracle_exact_id_equal_occurrences': oracle_equal,
            'primary_refined_occurrences': sum(x['refined'] for x in allrows),
            'recurrence_fallback_occurrences': recurrence_fallbacks,
            'topomodal_trunk_core_occurrences': len(core_rows),
            'nested_core_occurrences': len(core_rows),
            'topomodal_no_reportable_trunk_occurrences': recurrence_fallbacks - len(core_rows),
            'topomodal_trunk_strict_refinements': sum(x['core_refined'] for x in core_rows),
            'mean_parent_n': float(np.mean([x['parent_n'] for x in allrows])),
            'mean_primary_n': float(np.mean([x['output_n'] for x in allrows])),
            'mean_core_n': float(np.mean([x['topomodal_trunk_core_n'] for x in core_rows])) if core_rows else 0.0,
            'mean_core_ratio_to_primary': float(np.mean([x['core_ratio_to_primary'] for x in core_rows])) if core_rows else 0.0,
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
    print(json.dumps({'verdict': 'PASS_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_PRETRUTH', 'sha256': fr.sha(a.output), 'summary': payload['summary']}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
