#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from orbittrace_v40_component_best_evidence_representative_v1 import train_evaluate as v40

VARIANT = 'connected_component_multiplicity_calibrated_first_representative_v1'
CALIBRATION = 'q=1-(1-p_min)^m'


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def build_v41_order(
    route: str,
    base_order: list[str],
    components: list[dict[str, Any]],
    rank_maps: dict[str, dict[str, int]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Exact v40 representative architecture with #1083 multiplicity calibration only."""
    require(route in ('sugar', 'hdbscan'), 'invalid route')
    n_route = len(base_order)
    require(n_route == len(rank_maps[route]) and n_route > 1, 'rank universe mismatch')
    reps: list[dict[str, Any]] = []
    rep_ids: set[str] = set()

    for c in components:
        own_ids = list(map(str, c['sugar_family_ids'] if route == 'sugar' else c['hdbscan_family_ids']))
        if not own_ids:
            continue
        own_rep = min(own_ids, key=lambda fid: (rank_maps[route][fid], fid))
        rep_ids.add(own_rep)

        member_rows: list[tuple[str, str, int, float]] = []
        for fid in map(str, c['sugar_family_ids']):
            rr = int(rank_maps['sugar'][fid])
            p = float((rr - 1) / (len(rank_maps['sugar']) - 1))
            member_rows.append(('sugar', fid, rr, p))
        for fid in map(str, c['hdbscan_family_ids']):
            rr = int(rank_maps['hdbscan'][fid])
            p = float((rr - 1) / (len(rank_maps['hdbscan']) - 1))
            member_rows.append(('hdbscan', fid, rr, p))
        require(member_rows, 'empty component')

        best_member = min(member_rows, key=lambda x: (x[3], x[2], x[0], x[1]))
        p_min = float(best_member[3])
        m = int(c['member_count'])
        require(m == len(member_rows) and m >= 1, 'component multiplicity mismatch')
        q = float(1.0 - (1.0 - p_min) ** m)
        require(0.0 <= p_min <= 1.0 and 0.0 <= q <= 1.0, 'invalid calibrated component evidence')

        reps.append({
            'component_id': str(c['component_id']),
            # v40's parent evaluator sorts/records this generic field; in v41 it is q, not raw p_min.
            'component_evidence': q,
            'raw_component_min_percentile': p_min,
            'calibrated_component_evidence': q,
            'calibration_formula': CALIBRATION,
            'calibration_multiplicity': m,
            'representative_family_id': own_rep,
            'representative_v31_rank': int(rank_maps[route][own_rep]),
            'representative_v31_percentile': float((rank_maps[route][own_rep] - 1) / (n_route - 1)),
            'component_member_count': m,
            'component_sugar_member_count': int(c['sugar_member_count']),
            'component_hdbscan_member_count': int(c['hdbscan_member_count']),
            'best_evidence_route': best_member[0],
            'best_evidence_family_id': best_member[1],
            'best_evidence_v31_rank': int(best_member[2]),
            'best_evidence_percentile': p_min,
        })

    primary_rows = sorted(
        reps,
        key=lambda r: (
            float(r['calibrated_component_evidence']),
            int(r['representative_v31_rank']),
            str(r['component_id']),
        ),
    )
    primary = [str(r['representative_family_id']) for r in primary_rows]
    require(len(primary) == len(rep_ids) and len(primary) == len(set(primary)), f'{route} duplicate primary representative')
    secondary = [fid for fid in base_order if fid not in rep_ids]
    order = primary + secondary
    require(len(order) == len(base_order) and set(order) == set(base_order), f'{route} invalid v41 total order')
    for i, r in enumerate(primary_rows):
        r['v41_primary_position'] = i + 1
    return order, primary_rows


def pretruth_mode(sugar_root: Path, hdbscan_root: Path, output: Path) -> int:
    # No v41 pretruth change: exact v40/#1064/#1072 graph and component identity.
    return v40.pretruth_mode(sugar_root, hdbscan_root, output)


def evaluate_mode(
    sugar_root: Path,
    hdbscan_root: Path,
    truth_root: Path,
    ranker_source: Path,
    graph_file: Path,
    component_file: Path,
    output: Path,
) -> int:
    output.mkdir(parents=True, exist_ok=True)

    original_builder = v40.build_v40_order
    original_variant = v40.VARIANT
    v40.build_v40_order = build_v41_order
    v40.VARIANT = VARIANT
    try:
        rc = v40.evaluate_mode(
            sugar_root,
            hdbscan_root,
            truth_root,
            ranker_source,
            graph_file,
            component_file,
            output,
        )
    finally:
        v40.build_v40_order = original_builder
        v40.VARIANT = original_variant
    require(rc == 0, 'parent evaluator returned nonzero')

    parent_result_path = output / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_RESULT.json'
    parent_freeze_path = output / 'V40_COMPONENT_BEST_EVIDENCE_REPRESENTATIVE_MODEL_FREEZE.json'
    require(parent_result_path.exists() and parent_freeze_path.exists(), 'parent evaluator outputs missing')
    r = json.loads(parent_result_path.read_text())

    wins = int(r['panel_wins'])
    passed = wins == 4
    require(len(r['panels']) == 4 and r['parent_v31_reproduction_pass'] is True, 'parent controls missing')
    require(r['pretruth_graph_sha256'] == v40.GRAPH_SHA256, 'graph identity changed')
    require(r['pretruth_component_sha256'] == v40.COMPONENT_SHA256, 'component identity changed')

    for route in ('sugar', 'hdbscan'):
        rows = r['primary_component_rows'][route]
        require(rows, f'{route} missing primary component rows')
        for row in rows:
            require(row['calibration_formula'] == CALIBRATION, 'calibration formula changed')
            require(int(row['calibration_multiplicity']) == int(row['component_member_count']), 'calibration multiplicity changed')
            p = float(row['raw_component_min_percentile'])
            m = int(row['calibration_multiplicity'])
            q = float(row['calibrated_component_evidence'])
            require(abs(q - (1.0 - (1.0 - p) ** m)) < 1e-15, 'calibration value changed')
            require(abs(float(row['component_evidence']) - q) < 1e-15, 'parent sort field is not calibrated q')
        od = r['order_diagnostics'][route]
        od['v41_total_order_sha256'] = od.pop('v40_total_order_sha256')
        od['component_evidence_rule'] = 'q=1-(1-p_min)^m, where p_min is minimum normalized exact-v31 percentile over all frozen component members and m is total frozen component membership count'
        od['primary_sort'] = '(calibrated_component_evidence_q, representative_own_v31_rank, component_id)'

    # Convert the parent evaluator's reference artifact, if and only if v41 actually passed.
    parent_reference = output / 'v40_component_best_evidence_representative_reference.npz'
    v41_reference = output / 'v41_component_min_multiplicity_calibrated_representative_reference.npz'
    if passed:
        require(parent_reference.exists(), 'passing v41 parent reference missing')
        parent_reference.replace(v41_reference)
        freeze = {
            'verdict': 'PASS_V41_FULL_EXPOSED_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_REFERENCE_FREEZE',
            'reference_sha256': v40.v22.sha(v41_reference),
            'pretruth_graph_sha256': v40.GRAPH_SHA256,
            'pretruth_component_sha256': v40.COMPONENT_SHA256,
            'feature_dimension': v40.FEATURE_DIM,
            'k': 1,
            'distance': 'ordinary Euclidean after full-training z-score for v31; frozen radius-1 connected-component identity for component ordering',
            'annual_margin': 'd_nonpositive-d_positive',
            'annual_combiner': 'min(margin_2013,margin_2014)',
            'component_raw_evidence': 'minimum normalized exact-v31 rank percentile among all frozen component members',
            'component_calibration': CALIBRATION,
            'component_multiplicity': 'total frozen Sugar+HDB candidate vertices in component',
            'representative_rule': 'smallest own-route exact-v31 fused rank in component',
            'in_sample_reference_score_used_for_promotion': False,
        }
    else:
        require(not parent_reference.exists(), 'failed v41 unexpectedly produced a reference artifact')
        freeze = {
            'verdict': 'NOT_FROZEN_V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_FAIL',
            'reference_sha256': None,
        }

    r.update({
        'scientific_stage': 'EXPOSED_SONOTACO_V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_V1',
        'verdict': (
            'PASS_V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT'
            if passed else
            'FAIL_V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT'
        ),
        'sole_scientific_change': 'replace v40 raw minimum component evidence p_min with #1083 canonical minimum-order-statistic calibration q=1-(1-p_min)^m; all graph/component/representative/two-phase ordering machinery otherwise unchanged',
        'authorizing_diagnostic': '#1083 component-minimum multiplicity calibration diagnostic; q-based order and literature panels were not evaluated there',
        'promotion_variant': VARIANT,
        'component_evidence': 'q=1-(1-p_min)^m with p_min the minimum normalized exact-v31 rank percentile over all frozen component members and m the total frozen component membership count',
        'component_raw_evidence': 'minimum normalized exact-v31 rank percentile over all members of frozen component',
        'component_multiplicity': 'total Sugar+HDB candidate vertices in frozen connected component',
        'component_calibration_formula': CALIBRATION,
        'primary_order': 'all route component representatives sorted by (calibrated q, own representative v31 rank, component_id)',
        'full_model_freeze': freeze,
        'v40_parent_source_commit': '31704c312c09be2765ad3f65a0685d1acfd2b055',
        'v40_parent_source_blob': '710944a43111e72ed286b3a5c06010db619c807f',
        'multiplicity_calibration_diagnostic': '#1083 PASS_V40_COMPONENT_MIN_MULTIPLICITY_CALIBRATION_DIAGNOSTIC',
        'quality_suppression_used_for_ranking': False,
        'quality_suppression_diagnostic': '#1086 diagnostic-only; intentionally not fused into v41',
        'calibration_coefficient_search': False,
        'calibration_exponent_search': False,
        'calibration_pseudocount_search': False,
        'effective_component_size_search': False,
        'quality_prior_fusion_search': False,
        'quality_suppression_threshold_search': False,
    })

    v41_freeze_path = output / 'V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_MODEL_FREEZE.json'
    v41_result_path = output / 'V41_COMPONENT_MIN_MULTIPLICITY_CALIBRATED_REPRESENTATIVE_RESULT.json'
    v41_freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')
    v41_result_path.write_text(json.dumps(r, indent=2, sort_keys=True, allow_nan=False) + '\n')

    # Remove v40-labelled transient metadata so the artifact has one binding scientific result.
    parent_result_path.unlink()
    parent_freeze_path.unlink()

    print(json.dumps({
        'verdict': r['verdict'],
        'panel_wins': wins,
        'panels': r['panels'],
        'order_diagnostics': r['order_diagnostics'],
        'full_model_freeze': freeze,
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    g = sub.add_parser('pretruth')
    g.add_argument('--sugar-root', type=Path, required=True)
    g.add_argument('--hdbscan-root', type=Path, required=True)
    g.add_argument('--output', type=Path, required=True)
    e = sub.add_parser('evaluate')
    e.add_argument('--sugar-root', type=Path, required=True)
    e.add_argument('--hdbscan-root', type=Path, required=True)
    e.add_argument('--truth-root', type=Path, required=True)
    e.add_argument('--ranker-source', type=Path, required=True)
    e.add_argument('--graph-file', type=Path, required=True)
    e.add_argument('--component-file', type=Path, required=True)
    e.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pretruth':
        return pretruth_mode(a.sugar_root, a.hdbscan_root, a.output)
    return evaluate_mode(a.sugar_root, a.hdbscan_root, a.truth_root, a.ranker_source, a.graph_file, a.component_file, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
