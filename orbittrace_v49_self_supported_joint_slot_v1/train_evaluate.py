#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v48_self_supported_quality_component_transfer_v1 import train_evaluate as v48

v42 = v48.v42

VARIANT = 'v49_self_supported_joint_slot_v1'
HDB_N = 229
SUGAR_N = 267
JOINT_N = 60
SELF_SUPPORTED_N = 35
NONJOINT_N = 169
SIGNAL_SHA256 = 'a3bcea66b72003a38cc492ea3b182d92cd20f3d1b94a43acbc8a0cbdd465ed07'
GAP_RESULT_SHA256 = 'c372b4aac0547198cb6ac4239d604fddc12fdd0f11a930ab39a1e46d01f5e461'
GAP_VECTOR_SHA256 = '145ceb528e66f924c00c152cf2e5a38a2424ffda8f0a39a7eb80680c1bd5dadd'
GAP_VECTOR_CANONICAL_SHA256 = '0a9eda015ca367697a1dca678a0e8f7d986880fc424a0cbf4573567ab8776672'
V31_HDB_ORDER_SHA256 = '85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d'
V49_HDB_ORDER_SHA256 = '6948b51c1510add3819fb467118ff829bbe5ffcbd785538abd5a065af3f848c7'
AUTHOR_1139_RUN = 31488131546
AUTHOR_1139_ARTIFACT = 9099927842
AUTHOR_1139_DIGEST = 'sha256:67960fbd5fd76173da62c6d1823d507c99ee6431862ce56351aa7a194ec81e07'
V48_BINDING_RUN = 31489678337
V48_BINDING_ARTIFACT = 9100509632
V48_BINDING_DIGEST = 'sha256:6d30db98546cb61f26d864546f1e809c89ed40783039032e24f664a7a681b251'
V48_BINDING_RESULT_SHA256 = 'f663acf4adb21168b834989c803930029a9924b0788af63127ce91a0d3e1b359'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return v42.v40.v22.sha(path)


def order_sha(order: list[str]) -> str:
    return v42.v40.order_sha(list(map(str, order)))


def self_supported_values(r: dict[str, Any]) -> tuple[bool, bool, bool, float, float, int]:
    rv = int(r['v31_rank'])
    rq = int(r['quality_rank'])
    pv = float(r['v31_percentile'])
    pq = float(r['quality_percentile'])
    pc = float(r['component_best_v31_percentile'])
    require(np.isfinite(pv) and np.isfinite(pq) and np.isfinite(pc), 'nonfinite support percentile')
    require(0.0 <= pv <= 1.0 and 0.0 <= pq <= 1.0 and 0.0 <= pc <= 1.0, 'invalid support percentile')
    quality_suppressed = bool(rq < rv)
    component_opportunity = bool(pc < pv)
    joint = bool(quality_suppressed and component_opportunity)
    quality_suppression = float(pv - pq)
    inheritance_gap = float(pv - pc)
    self_supported = bool(joint and pq <= pc)
    require(self_supported == bool(joint and quality_suppression >= inheritance_gap), 'self-support algebra changed')
    priority_key = int(rq if self_supported else rv)
    return joint, self_supported, quality_suppressed, quality_suppression, inheritance_gap, priority_key


def build_v49_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    require(route in ('sugar', 'hdbscan'), 'invalid route')
    if route == 'sugar':
        rows = [
            {
                'representative_family_id': str(fid),
                'family_id': str(fid),
                'v31_rank': i + 1,
                'v42_key': i + 1,
                'v42_rank': i + 1,
                'joint_gate': False,
                'original_joint_gate': False,
                'self_supported_gate': False,
                'sugar_unchanged': True,
            }
            for i, fid in enumerate(base_order)
        ]
        return list(map(str, base_order)), rows

    qrank = dict(v42._QUALITY_RANK)
    require(len(base_order) == HDB_N and set(map(str, base_order)) == set(qrank), 'HDB quality map not initialized on exact universe')
    vrank = rank_maps['hdbscan']
    component_best = v42.component_best_percentiles(components, rank_maps)
    hdb_component: dict[str, str] = {}
    for c in components:
        cid = str(c['component_id'])
        for fid in map(str, c['hdbscan_family_ids']):
            require(fid not in hdb_component, 'HDB family occurs in multiple components')
            hdb_component[fid] = cid
    require(set(hdb_component) == set(map(str, base_order)), 'HDB component assignment incomplete')

    rows: list[dict[str, Any]] = []
    for fid0 in base_order:
        fid = str(fid0)
        rv = int(vrank[fid])
        rq = int(qrank[fid])
        pv = float((rv - 1) / (HDB_N - 1))
        pq = float((rq - 1) / (HDB_N - 1))
        cid = hdb_component[fid]
        pc = float(component_best[cid])
        seed = {
            'v31_rank': rv,
            'quality_rank': rq,
            'v31_percentile': pv,
            'quality_percentile': pq,
            'component_best_v31_percentile': pc,
        }
        joint, self_supported, quality_suppressed, quality_suppression, inheritance_gap, key = self_supported_values(seed)
        component_opportunity = bool(pc < pv)
        rows.append({
            'representative_family_id': fid,
            'family_id': fid,
            'component_id': cid,
            'v31_rank': rv,
            'quality_rank': rq,
            'v31_percentile': pv,
            'quality_percentile': pq,
            'component_best_v31_percentile': pc,
            'quality_suppression': quality_suppression,
            'inheritance_gap': inheritance_gap,
            'quality_suppressed': quality_suppressed,
            'component_opportunity': component_opportunity,
            'original_joint_gate': joint,
            'self_supported_gate': self_supported,
            'joint_gate': self_supported,
            'v42_key': key,
            'promotion_rank_gain': int(rv - key) if self_supported else 0,
        })

    by_id = {str(r['family_id']): r for r in rows}
    joint_ids = [str(fid) for fid in map(str, base_order) if bool(by_id[str(fid)]['original_joint_gate'])]
    require(len(joint_ids) == JOINT_N, 'original joint-positive HDB count changed')
    require(sum(bool(by_id[fid]['self_supported_gate']) for fid in joint_ids) == SELF_SUPPORTED_N, 'self-supported HDB count changed')
    joint_positions = sorted(int(vrank[fid]) for fid in joint_ids)
    ordered_joint = sorted(
        joint_ids,
        key=lambda fid: (
            int(by_id[fid]['v42_key']),
            int(by_id[fid]['v31_rank']),
            fid,
        ),
    )

    order = list(map(str, base_order))
    for pos, fid in zip(joint_positions, ordered_joint):
        order[pos - 1] = fid
    require(len(order) == HDB_N and len(set(order)) == HDB_N and set(order) == set(map(str, base_order)), 'invalid v49 HDB permutation')

    joint_set = set(joint_ids)
    joint_position_set = set(joint_positions)
    for pos, old_fid in enumerate(map(str, base_order), start=1):
        if pos not in joint_position_set:
            require(order[pos - 1] == old_fid, f'nonjoint v31 slot moved at position {pos}')
            require(old_fid not in joint_set, f'joint family unexpectedly occupied nonjoint v31 slot {pos}')
        else:
            require(order[pos - 1] in joint_set, f'nonjoint family entered joint slot {pos}')

    new_rank = {fid: i + 1 for i, fid in enumerate(order)}
    require(sorted(new_rank[fid] for fid in joint_ids) == joint_positions, 'joint slot set changed')
    require(order_sha(order) == V49_HDB_ORDER_SHA256, 'runtime v49 HDB order changed')
    for r in rows:
        fid = str(r['family_id'])
        r['v42_rank'] = int(new_rank[fid])
        r['v49_rank'] = int(new_rank[fid])
        r['v49_rank_delta'] = int(r['v31_rank'] - r['v49_rank'])
        r['v49_joint_slot_position'] = int(r['v49_rank']) if bool(r['original_joint_gate']) else None
        if not bool(r['original_joint_gate']):
            require(int(r['v49_rank']) == int(r['v31_rank']), f'nonjoint family moved: {fid}')
    return order, rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    return v48.pretruth_mode(sugar_root, hdbscan_root, output)


def freeze_order_mode(signal_file: Path, gap_result: Path, gap_vector: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    signal = v48.load_signal(signal_file)
    _, vector = v48.validate_1139(gap_result, gap_vector)
    rows_by_id = {str(r['family_id']): r for r in signal['families']}
    require(len(rows_by_id) == HDB_N, 'duplicate #1098 HDB family id')
    v31_order = sorted(rows_by_id, key=lambda fid: (int(rows_by_id[fid]['v31_rank']), fid))
    require(order_sha(v31_order) == V31_HDB_ORDER_SHA256, 'exact v31 HDB order changed')
    joint_ids = [fid for fid in v31_order if bool(rows_by_id[fid]['joint_signal'])]
    require(len(joint_ids) == JOINT_N, '#1098 joint count changed')
    vector_by_id = {str(r['family_id']): r for r in vector['families']}
    require(set(joint_ids) == set(vector_by_id), '#1098/#1139 joint identity mismatch')

    priority: dict[str, int] = {}
    self_supported: dict[str, bool] = {}
    frozen_rows: list[dict[str, Any]] = []
    for fid in joint_ids:
        r = rows_by_id[fid]
        vr = vector_by_id[fid]
        joint, ss, quality_suppressed, quality_suppression, inheritance_gap, key = self_supported_values(r)
        require(joint is True and bool(r['joint_signal']) is True, 'joint identity changed')
        require(bool(r['positive_quality_suppression']) == quality_suppressed, 'quality suppression identity changed')
        require(bool(r['component_closure_opportunity']) is True, 'component opportunity identity changed')
        require(abs(float(vr['inheritance_gap']) - inheritance_gap) < 1e-15, '#1139 inheritance gap changed')
        require(abs(float(vr['v31_percentile']) - float(r['v31_percentile'])) < 1e-15, '#1139 v31 percentile changed')
        require(abs(float(vr['component_best_v31_percentile']) - float(r['component_best_v31_percentile'])) < 1e-15, '#1139 component-best percentile changed')
        priority[fid] = int(key)
        self_supported[fid] = bool(ss)
        frozen_rows.append({
            'family_id': fid,
            'v31_rank': int(r['v31_rank']),
            'quality_rank': int(r['quality_rank']),
            'v31_percentile': float(r['v31_percentile']),
            'quality_percentile': float(r['quality_percentile']),
            'component_best_v31_percentile': float(r['component_best_v31_percentile']),
            'quality_suppression': quality_suppression,
            'inheritance_gap': inheritance_gap,
            'self_supported_gate': bool(ss),
            'priority_key': int(key),
        })
    require(sum(self_supported.values()) == SELF_SUPPORTED_N, 'truth-blind self-supported count changed')

    joint_positions = sorted(int(rows_by_id[fid]['v31_rank']) for fid in joint_ids)
    ordered_joint = sorted(joint_ids, key=lambda fid: (priority[fid], int(rows_by_id[fid]['v31_rank']), fid))
    v49_order = list(v31_order)
    for pos, fid in zip(joint_positions, ordered_joint):
        v49_order[pos - 1] = fid
    require(order_sha(v49_order) == V49_HDB_ORDER_SHA256, 'truth-blind v49 HDB order changed')
    joint_position_set = set(joint_positions)
    joint_set = set(joint_ids)
    for pos, old_fid in enumerate(v31_order, start=1):
        if pos not in joint_position_set:
            require(v49_order[pos - 1] == old_fid and old_fid not in joint_set, f'nonjoint position changed at {pos}')
        else:
            require(v49_order[pos - 1] in joint_set, f'joint slot contamination at {pos}')
    new_rank = {fid: i + 1 for i, fid in enumerate(v49_order)}
    require(sorted(new_rank[fid] for fid in joint_ids) == joint_positions, 'truth-blind joint slot set changed')
    moved = int(sum(v49_order[i] != v31_order[i] for i in range(HDB_N)))
    require(moved == 59, 'truth-blind moved count changed')

    prefix_diagnostics: dict[str, Any] = {}
    for k in (9, 11):
        a = set(v31_order[:k])
        b = set(v49_order[:k])
        incoming = len(b - a)
        outgoing = len(a - b)
        require(incoming == 1 and outgoing == 1, f'truth-blind top-{k} leverage changed')
        prefix_diagnostics[f'top{k}'] = {
            'budget': k,
            'intersection_count': len(a & b),
            'incoming_count': incoming,
            'outgoing_count': outgoing,
            'membership_changed': True,
            'identities_serialized': False,
        }

    freeze = {
        'verdict': 'PASS_V49_SELF_SUPPORTED_JOINT_SLOT_ORDER_FREEZE',
        'scientific_role': 'V49_COMPLETE_HDB_ORDER_AND_FIXED_JOINT_SLOTS_FROZEN_BEFORE_OUTCOME_TRUTH',
        'source_1098_signal_sha256': SIGNAL_SHA256,
        'authorizing_1139_run': AUTHOR_1139_RUN,
        'authorizing_1139_artifact': AUTHOR_1139_ARTIFACT,
        'authorizing_1139_artifact_digest': AUTHOR_1139_DIGEST,
        'authorizing_1139_result_sha256': GAP_RESULT_SHA256,
        'authorizing_1139_vector_sha256': GAP_VECTOR_SHA256,
        'authorizing_1139_vector_canonical_sha256': GAP_VECTOR_CANONICAL_SHA256,
        'v48_binding_run_motivation_only': V48_BINDING_RUN,
        'v48_binding_artifact_motivation_only': V48_BINDING_ARTIFACT,
        'v48_binding_artifact_digest_motivation_only': V48_BINDING_DIGEST,
        'v48_binding_result_sha256_motivation_only': V48_BINDING_RESULT_SHA256,
        'hdb_family_count': HDB_N,
        'joint_positive_candidate_count': JOINT_N,
        'self_supported_candidate_count': SELF_SUPPORTED_N,
        'nonjoint_candidate_count': NONJOINT_N,
        'v31_hdb_order_sha256': V31_HDB_ORDER_SHA256,
        'v49_hdb_order_sha256': V49_HDB_ORDER_SHA256,
        'moved_candidate_count': moved,
        'joint_slot_count': len(joint_positions),
        'joint_slot_set_unchanged': True,
        'nonjoint_positions_unchanged': True,
        'self_supported_condition': 'joint_signal AND quality_percentile <= component_best_v31_percentile',
        'equivalent_gain_condition': 'quality_suppression >= inheritance_gap',
        'joint_priority': '(quality_rank if self_supported else exact_v31_rank, exact_v31_rank, family_id)',
        'slot_rule': 'permute the exact 60 #1098 joint identities only across their exact v31 occupied positions',
        'prefix_diagnostics': prefix_diagnostics,
        'hdb_order': v49_order,
        'joint_candidate_rows': frozen_rows,
        'truth_accessed': False,
        'outcome_identity_used': False,
        'year_specific_rule': False,
        'budget_specific_rule': False,
        'alternate_slot_set_evaluated': False,
        'slot_expansion': False,
        'slot_contraction': False,
        'alternate_self_support_inequality_search': False,
        'threshold_selected': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'coefficient_selected': False,
        'oracle_identity_used_for_ranking': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V49_SELF_SUPPORTED_JOINT_SLOT_ORDER_FREEZE.json').write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': freeze['verdict'],
        'joint_positive_candidate_count': JOINT_N,
        'self_supported_candidate_count': SELF_SUPPORTED_N,
        'moved_candidate_count': moved,
        'v49_hdb_order_sha256': V49_HDB_ORDER_SHA256,
        'prefix_diagnostics': prefix_diagnostics,
    }, indent=2, sort_keys=True))
    return 0


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    authorizing_1091: Path,
    authorizing_1139: Path,
    vector_1139: Path,
    frozen_order: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)
    v48.validate_1139(authorizing_1139, vector_1139)
    f = json.loads(frozen_order.read_text())
    require(f['verdict'] == 'PASS_V49_SELF_SUPPORTED_JOINT_SLOT_ORDER_FREEZE', 'v49 pretruth order freeze missing')
    require(f['scientific_role'] == 'V49_COMPLETE_HDB_ORDER_AND_FIXED_JOINT_SLOTS_FROZEN_BEFORE_OUTCOME_TRUTH', 'v49 order freeze role changed')
    require(int(f['joint_positive_candidate_count']) == JOINT_N and int(f['self_supported_candidate_count']) == SELF_SUPPORTED_N, 'v49 frozen gate counts changed')
    require(int(f['nonjoint_candidate_count']) == NONJOINT_N and int(f['moved_candidate_count']) == 59, 'v49 frozen containment counts changed')
    require(f['joint_slot_set_unchanged'] is True and f['nonjoint_positions_unchanged'] is True, 'v49 frozen slot containment changed')
    require(f['v31_hdb_order_sha256'] == V31_HDB_ORDER_SHA256 and f['v49_hdb_order_sha256'] == V49_HDB_ORDER_SHA256, 'v49 frozen order identity changed')
    require(f['truth_accessed'] is False and f['outcome_identity_used'] is False, 'v49 order was not frozen truth-free')
    for k in ('top9', 'top11'):
        d = f['prefix_diagnostics'][k]
        require(int(d['incoming_count']) == 1 and int(d['outgoing_count']) == 1 and d['membership_changed'] is True, f'{k} frozen leverage changed')
        require(d['identities_serialized'] is False, f'{k} identity serialization changed')

    original_builder = v42.build_v42_order
    original_variant = v42.VARIANT
    v42.build_v42_order = build_v49_order
    v42.VARIANT = VARIANT
    engine = output / '_frozen_v42_engine'
    try:
        rc = v42.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            authorizing_1091,
            engine,
        )
    finally:
        v42.build_v42_order = original_builder
        v42.VARIANT = original_variant
    require(rc == 0, 'frozen v42 execution engine failed')

    raw_path = engine / 'V42_QUALITY_COMPONENT_GATED_RESCUE_RESULT.json'
    require(raw_path.is_file(), 'frozen v42 engine result missing')
    raw = json.loads(raw_path.read_text())
    require(raw['parent_v31_reproduction_pass'] is True and len(raw['parent_v31_controls']) == 4, 'exact v31 parent reproduction failed')
    require(raw['pretruth_graph_sha256'] == v42.v40.GRAPH_SHA256 and raw['pretruth_component_sha256'] == v42.v40.COMPONENT_SHA256, 'frozen geometry changed')
    require(raw['sugar_rule'] == 'exact v31 unchanged', 'Sugar rule changed')

    hdb_rows = list(raw['hdb_candidate_rows'])
    require(len(hdb_rows) == HDB_N, 'HDB row count changed')
    require(sum(bool(x['original_joint_gate']) for x in hdb_rows) == JOINT_N, 'runtime original joint count changed')
    require(sum(bool(x['self_supported_gate']) for x in hdb_rows) == SELF_SUPPORTED_N, 'runtime self-supported count changed')
    hdb_v31_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda x: int(x['v31_rank']))]
    hdb_v49_order = [str(x['family_id']) for x in sorted(hdb_rows, key=lambda x: int(x['v42_rank']))]
    require(order_sha(hdb_v31_order) == V31_HDB_ORDER_SHA256, 'runtime v31 HDB order changed')
    require(order_sha(hdb_v49_order) == V49_HDB_ORDER_SHA256, 'evaluated HDB order differs from v49 freeze')
    require(hdb_v49_order == list(map(str, f['hdb_order'])), 'evaluated HDB identities differ from v49 freeze')

    by_id = {str(x['family_id']): x for x in hdb_rows}
    joint_ids = [fid for fid in hdb_v31_order if bool(by_id[fid]['original_joint_gate'])]
    nonjoint_ids = [fid for fid in hdb_v31_order if not bool(by_id[fid]['original_joint_gate'])]
    require(len(joint_ids) == JOINT_N and len(nonjoint_ids) == NONJOINT_N, 'runtime joint partition changed')
    v31_joint_positions = sorted(int(by_id[fid]['v31_rank']) for fid in joint_ids)
    v49_joint_positions = sorted(int(by_id[fid]['v42_rank']) for fid in joint_ids)
    require(v31_joint_positions == v49_joint_positions, 'runtime joint slot set changed')
    require(all(int(by_id[fid]['v42_rank']) == int(by_id[fid]['v31_rank']) for fid in nonjoint_ids), 'runtime nonjoint position moved')
    moved = int(sum(hdb_v31_order[i] != hdb_v49_order[i] for i in range(HDB_N)))
    require(moved == 59, 'runtime moved count changed')

    prefix_diagnostics: dict[str, Any] = {}
    for k in (9, 11):
        a = set(hdb_v31_order[:k])
        b = set(hdb_v49_order[:k])
        require(len(b - a) == 1 and len(a - b) == 1, f'runtime top-{k} leverage changed')
        prefix_diagnostics[f'top{k}'] = {
            'budget': k,
            'intersection_count': len(a & b),
            'incoming_count': len(b - a),
            'outgoing_count': len(a - b),
            'membership_changed': True,
        }

    panels = list(raw['panels'])
    require(len(panels) == 4, 'panel count changed')
    wins = int(sum(bool(x['superiority_pair_pass']) for x in panels))
    passed = bool(wins == 4)
    freeze: dict[str, Any] = {'verdict': 'NOT_FROZEN_V49_SELF_SUPPORTED_JOINT_SLOT_FAIL', 'reference_sha256': None}
    engine_ref = engine / 'v42_quality_component_gated_rescue_reference.npz'
    if passed:
        require(engine_ref.is_file(), 'passing engine reference missing')
        dst = output / 'v49_self_supported_joint_slot_reference.npz'
        shutil.copyfile(engine_ref, dst)
        freeze = {
            'verdict': 'PASS_V49_FULL_EXPOSED_SELF_SUPPORTED_JOINT_SLOT_REFERENCE_FREEZE',
            'reference_sha256': sha(dst),
            'v49_hdb_order_sha256': V49_HDB_ORDER_SHA256,
            'joint_positive_candidate_count': JOINT_N,
            'self_supported_candidate_count': SELF_SUPPORTED_N,
            'nonjoint_candidate_count': NONJOINT_N,
            'joint_slot_set_unchanged': True,
            'nonjoint_positions_unchanged': True,
        }

    result = {
        'scientific_stage': 'EXPOSED_SONOTACO_V49_SELF_SUPPORTED_JOINT_SLOT_V1',
        'verdict': 'PASS_V49_SELF_SUPPORTED_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V49_SELF_SUPPORTED_JOINT_SLOT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change': 'contain exact v48 self-supported priority inside the exact 60 #1098 v31 joint slots; every nonjoint HDB position and Sugar remain exact v31',
        'authorizing_1091_run': 31456963941,
        'authorizing_1091_artifact': 9088402091,
        'authorizing_1091_sha256': '2edb949dbab2d7cbf6ed5e808e2a049116eb0934b25b356572463b615d730842',
        'authorizing_1139_run': AUTHOR_1139_RUN,
        'authorizing_1139_artifact': AUTHOR_1139_ARTIFACT,
        'authorizing_1139_artifact_digest': AUTHOR_1139_DIGEST,
        'authorizing_1139_result_sha256': GAP_RESULT_SHA256,
        'authorizing_1139_vector_sha256': GAP_VECTOR_SHA256,
        'authorizing_1139_vector_canonical_sha256': GAP_VECTOR_CANONICAL_SHA256,
        'v48_binding_run_motivation_only': V48_BINDING_RUN,
        'v48_binding_artifact_motivation_only': V48_BINDING_ARTIFACT,
        'v48_binding_artifact_digest_motivation_only': V48_BINDING_DIGEST,
        'v48_binding_result_sha256_motivation_only': V48_BINDING_RESULT_SHA256,
        'pretruth_graph_sha256': raw['pretruth_graph_sha256'],
        'pretruth_component_sha256': raw['pretruth_component_sha256'],
        'parent_v31_reproduction_pass': True,
        'parent_v31_controls': raw['parent_v31_controls'],
        'sugar_rule': 'exact v31 unchanged',
        'sugar_modified': False,
        'hdb_family_count': HDB_N,
        'hdb_original_joint_candidate_count': JOINT_N,
        'hdb_self_supported_candidate_count': SELF_SUPPORTED_N,
        'hdb_nonjoint_candidate_count': NONJOINT_N,
        'hdb_self_supported_condition': 'joint_signal AND quality_percentile <= component_best_v31_percentile',
        'hdb_equivalent_gain_condition': 'quality_suppression >= inheritance_gap',
        'hdb_joint_priority': '(quality_rank if self_supported else exact_v31_rank, exact_v31_rank, family_id)',
        'hdb_slot_rule': 'permute exact 60 #1098 joint identities only across their exact v31 occupied positions',
        'joint_slot_set_unchanged': True,
        'nonjoint_positions_unchanged': True,
        'moved_candidate_count': moved,
        'v31_hdb_order_sha256': V31_HDB_ORDER_SHA256,
        'v49_hdb_order_sha256': V49_HDB_ORDER_SHA256,
        'prefix_diagnostics': prefix_diagnostics,
        'panel_wins': wins,
        'panels': panels,
        'hdb_candidate_rows': hdb_rows,
        'full_model_freeze': freeze,
        'alternate_self_support_inequality_search': False,
        'strict_vs_nonstrict_search': False,
        'epsilon_or_tolerance_relaxation': False,
        'inheritance_gap_threshold_search': False,
        'quality_suppression_threshold_search': False,
        'component_threshold_search': False,
        'partial_promotion_search': False,
        'interpolation_search': False,
        'coefficient_search': False,
        'bonus_or_cap_search': False,
        'weighted_fusion_search': False,
        'top_k_selected': False,
        'rank_window_selected': False,
        'budget_specific_rule': False,
        'year_specific_rule': False,
        'identity_exception_used': False,
        'boundary_rescue_list_created': False,
        'slot_expansion': False,
        'slot_contraction': False,
        'alternate_slot_set_evaluated': False,
        'second_pareto_layer_evaluated': False,
        'component_best_priority_retry': False,
        'v45_retry': False,
        'v47_retry': False,
        'global_v48_retry': False,
        'alternate_quality_order_search': False,
        'radius_search': False,
        'metric_search': False,
        'graph_pruning': False,
        'graph_expansion': False,
        'component_definition_search': False,
        'candidate_generation_changed': False,
        'candidate_membership_changed': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'annual_combiner_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_used_for_ranking': False,
        'truth_aware_group_identity_used_for_ranking': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V49_SELF_SUPPORTED_JOINT_SLOT_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({
        'verdict': result['verdict'],
        'panel_wins': wins,
        'moved_candidate_count': moved,
        'prefix_diagnostics': prefix_diagnostics,
        'panels': panels,
        'v49_hdb_order_sha256': V49_HDB_ORDER_SHA256,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    f = sub.add_parser('freeze-order')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--gap-result', type=Path, required=True)
    f.add_argument('--gap-vector', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--authorizing-1091', type=Path, required=True)
    e.add_argument('--authorizing-1139', type=Path, required=True)
    e.add_argument('--vector-1139', type=Path, required=True)
    e.add_argument('--frozen-order', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    if a.mode == 'freeze-order':
        return freeze_order_mode(a.signal_file, a.gap_result, a.gap_vector, a.output)
    return evaluate_mode(
        a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source,
        a.graph_file, a.component_file, a.authorizing_1091,
        a.authorizing_1139, a.vector_1139, a.frozen_order, a.output,
    )


if __name__ == '__main__':
    raise SystemExit(main())