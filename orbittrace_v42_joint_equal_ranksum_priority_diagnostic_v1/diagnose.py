#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

SOURCE_RUN = 31457788803
SOURCE_ARTIFACT = 9088683367
SOURCE_ARTIFACT_DIGEST = 'sha256:1ad3513e021136b402e8aa121faa37675e2982d57aa2a14f1bc5e28d81b61b11'
SOURCE_SIGNAL_SHA = '47966ec3e5b29f56c5bb536ed19f24a99ff41f11bc2d20778240b16c5e44fd47'
GRAPH_SHA256 = '2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25'
COMPONENT_SHA256 = 'c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd'
RECOVERY = 0.5


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def canonical_sha_without_self(obj: dict[str, Any]) -> str:
    x = dict(obj)
    x.pop('canonical_sha256_without_self_field', None)
    raw = json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'
    return hashlib.sha256(raw.encode()).hexdigest()


def auc_lower_better(rows: list[dict[str, Any]], recoverable_key: str, score_key: str) -> float:
    pos = [r for r in rows if bool(r[recoverable_key])]
    neg = [r for r in rows if not bool(r[recoverable_key])]
    require(pos and neg, f'empty AUC class for {recoverable_key}')
    wins = 0.0
    total = len(pos) * len(neg)
    for p in pos:
        ps = float(p[score_key])
        for n in neg:
            ns = float(n[score_key])
            if ps < ns:
                wins += 1.0
            elif ps == ns:
                wins += 0.5
    return float(wins / total)


def freeze_mode(signal_file: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    src = json.loads(signal_file.read_text())
    require(src['verdict'] == 'PASS_V31_QUALITY_COMPONENT_JOINT_UNIVERSE_SIGNAL_FREEZE', 'source signal verdict changed')
    require(src['scientific_role'] == 'FULL_FIXED_HDB_FAMILY_SIGNAL_VECTOR_NO_OUTCOME_USED_FOR_DEFINITION', 'source signal role changed')
    require(int(src['family_count']) == 229 and len(src['families']) == 229, 'source family universe changed')
    require(src['joint_signal_definition'] == '(v31_percentile > quality_percentile) AND (component_best_v31_percentile < v31_percentile)', 'source joint definition changed')
    require(src['graph_sha256'] == GRAPH_SHA256 and src['component_sha256'] == COMPONENT_SHA256, 'source graph/component identity changed')
    require(src['threshold_selected'] is False and src['top_k_selected'] is False and src['rank_window_selected'] is False and src['alternate_boolean_rule_evaluated'] is False and src['oracle_identity_hardcoded'] is False, 'source signal contains selected rescue rule')
    require(canonical_sha_without_self(src) == SOURCE_SIGNAL_SHA, 'source canonical signal SHA changed')
    require(src['canonical_sha256_without_self_field'] == SOURCE_SIGNAL_SHA, 'source self-recorded signal SHA changed')
    require(src['target_information_access'] is False and src['target_region_events_accessed'] is False and src['maarsy_scientific_access'] is False and src['dms_scientific_access'] is False, 'source protected access changed')
    require(src['blind_exclusion'] == [20.0, 55.0], 'source blind exclusion changed')

    joint = [r for r in src['families'] if bool(r['joint_signal'])]
    require(len(joint) == 60, 'joint-positive source breadth changed')
    rows = []
    for r in joint:
        pq = float(r['quality_percentile'])
        pc = float(r['component_best_v31_percentile'])
        e = 0.5 * (pq + pc)
        rows.append({
            'family_id': str(r['family_id']),
            'v31_rank': int(r['v31_rank']),
            'quality_rank': int(r['quality_rank']),
            'quality_percentile': pq,
            'component_id': str(r['component_id']),
            'component_best_v31_percentile': pc,
            'equal_ranksum_priority': float(e),
        })
    rows.sort(key=lambda r: (float(r['equal_ranksum_priority']), int(r['v31_rank']), str(r['family_id'])))
    for i, r in enumerate(rows):
        r['equal_ranksum_priority_rank_within_joint'] = i + 1

    freeze = {
        'verdict': 'PASS_V42_JOINT_EQUAL_RANKSUM_PRIORITY_FREEZE',
        'scientific_role': 'FROZEN_JOINT_POSITIVE_PRIORITY_VECTOR_BEFORE_OUTCOME_TRUTH',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_artifact_digest': SOURCE_ARTIFACT_DIGEST,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'graph_sha256': GRAPH_SHA256,
        'component_sha256': COMPONENT_SHA256,
        'family_universe_count': 229,
        'joint_positive_count': 60,
        'priority_definition': 'equal_ranksum_priority=(quality_percentile+component_best_v31_percentile)/2',
        'priority_direction': 'lower_is_better',
        'rows': rows,
        'truth_accessed': False,
        'candidate_total_order_evaluated': False,
        'literature_panel_evaluated': False,
        'alternative_aggregation_search': False,
        'weight_search': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'oracle_identity_hardcoded': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    out = output / 'V42_JOINT_EQUAL_RANKSUM_PRIORITY_FREEZE.json'
    out.write_text(json.dumps(freeze, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': freeze['verdict'], 'joint_positive_count': 60, 'priority_definition': freeze['priority_definition']}, indent=2, sort_keys=True))
    return 0


def diagnose_mode(freeze_file: Path, hdb_root: Path, truth_root: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    fr = json.loads(freeze_file.read_text())
    require(fr['verdict'] == 'PASS_V42_JOINT_EQUAL_RANKSUM_PRIORITY_FREEZE' and fr['truth_accessed'] is False, 'invalid frozen priority vector')
    require(fr['source_signal_sha256'] == SOURCE_SIGNAL_SHA and fr['joint_positive_count'] == 60, 'frozen priority identity changed')
    require(fr['priority_definition'] == 'equal_ranksum_priority=(quality_percentile+component_best_v31_percentile)/2', 'priority definition changed')
    require(fr['candidate_total_order_evaluated'] is False and fr['literature_panel_evaluated'] is False, 'priority freeze evaluated order/panel')

    import orbittrace_v40_component_best_evidence_representative_v1.train_evaluate as v40

    fp = json.loads((hdb_root / 'family_memberships.json').read_text())
    meta = json.loads((hdb_root / 'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
    ids = list(map(str, meta['family_ids']))
    fams = fp['families']
    require(meta['truth_accessed'] is False and fp['truth_accessed'] is False, 'HDB source payload truth flag changed')
    require(len(ids) == 229 and [str(f['family_id']) for f in fams] == ids, 'HDB fixed family identity changed')
    frozen_ids = {str(r['family_id']) for r in fr['rows']}
    require(len(frozen_ids) == 60 and frozen_ids.issubset(set(ids)), 'priority family identity changed')

    by_year = {year: json.loads((truth_root / f'truth_hdbscan_{year}.json').read_text()) for year in (2013, 2014)}
    eligible = v40.v22.eligible_from_year_truth(by_year)
    hidden: dict[str, str] = {}
    hidden.update(by_year[2013]); hidden.update(by_year[2014])
    priority_by_id = {str(r['family_id']): float(r['equal_ranksum_priority']) for r in fr['rows']}

    all_truth_rows = []
    for fam in fams:
        fid = str(fam['family_id'])
        t = v40.v22.family_truth(fam, hidden, eligible)
        label = t['best_label']
        if t['positive'] and label is not None:
            f13, f14 = map(float, v40.v24.annual_f1_for_fixed_label(fam, str(label), by_year))
            group = 'SHOWER/' + str(label)
        else:
            f13 = f14 = 0.0
            group = 'NEG/' + fid
        all_truth_rows.append({
            'family_id': fid,
            'diagnostic_group': group,
            'joint_positive': fid in frozen_ids,
            'equal_ranksum_priority': priority_by_id.get(fid),
            'annual_f1_2013': f13,
            'annual_f1_2014': f14,
            'recoverable_2013': bool(f13 > RECOVERY),
            'recoverable_2014': bool(f14 > RECOVERY),
        })

    joint_rows = [r for r in all_truth_rows if r['joint_positive']]
    require(len(joint_rows) == 60, 'truth join changed joint-positive count')
    annual = {}
    gates = []
    for year in (2013, 2014):
        rk = f'recoverable_{year}'
        pos = [r for r in joint_rows if r[rk]]
        neg = [r for r in joint_rows if not r[rk]]
        require(pos and neg, f'{year} family AUC lacks classes')
        auc_family = auc_lower_better(joint_rows, rk, 'equal_ranksum_priority')

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in all_truth_rows:
            grouped[str(r['diagnostic_group'])].append(r)
        group_rows = []
        for g, members in sorted(grouped.items()):
            joint_members = [r for r in members if r['joint_positive']]
            if not joint_members:
                continue
            group_rows.append({
                'diagnostic_group': g,
                'joint_family_count': len(joint_members),
                'equal_ranksum_priority': float(min(float(r['equal_ranksum_priority']) for r in joint_members)),
                'recoverable': bool(any(r[rk] for r in members)),
            })
        require(group_rows, f'{year} no joint-positive diagnostic groups')
        gpos = [r for r in group_rows if r['recoverable']]
        gneg = [r for r in group_rows if not r['recoverable']]
        require(gpos and gneg, f'{year} group AUC lacks classes')
        auc_group = auc_lower_better(group_rows, 'recoverable', 'equal_ranksum_priority')
        gate = bool(auc_family > 0.5 and auc_group > 0.5)
        gates.append(gate)
        annual[str(year)] = {
            'interpretation_gate_pass': gate,
            'family_level': {
                'joint_family_count': len(joint_rows),
                'recoverable_count': len(pos),
                'nonrecoverable_count': len(neg),
                'auc_lower_equal_ranksum_priority_predicts_recoverability': auc_family,
                'median_equal_ranksum_priority_recoverable': float(median(float(r['equal_ranksum_priority']) for r in pos)),
                'median_equal_ranksum_priority_nonrecoverable': float(median(float(r['equal_ranksum_priority']) for r in neg)),
            },
            'diagnostic_group_level': {
                'joint_group_count': len(group_rows),
                'recoverable_count': len(gpos),
                'nonrecoverable_count': len(gneg),
                'auc_lower_equal_ranksum_priority_predicts_recoverability': auc_group,
                'median_equal_ranksum_priority_recoverable': float(median(float(r['equal_ranksum_priority']) for r in gpos)),
                'median_equal_ranksum_priority_nonrecoverable': float(median(float(r['equal_ranksum_priority']) for r in gneg)),
            },
        }

    supported = bool(all(gates))
    result = {
        'verdict': 'PASS_V42_JOINT_EQUAL_RANKSUM_PRIORITY_DIAGNOSTIC' if supported else 'FAIL_V42_JOINT_EQUAL_RANKSUM_PRIORITY_DIAGNOSTIC',
        'scientific_role': 'POST_RESULT_PRIORITY_DIAGNOSTIC_ONLY_NO_CANDIDATE_TOTAL_ORDER_OR_PANEL_EVALUATED',
        'source_run': SOURCE_RUN,
        'source_artifact': SOURCE_ARTIFACT,
        'source_artifact_digest': SOURCE_ARTIFACT_DIGEST,
        'source_signal_sha256': SOURCE_SIGNAL_SHA,
        'joint_positive_count': 60,
        'priority_definition': fr['priority_definition'],
        'priority_direction_supported_both_years': supported,
        'interpretation_gate': 'AUC_family>0.5 AND AUC_group>0.5 in each of 2013 and 2014; no minimum margin or p-value',
        'annual_diagnostics': annual,
        'candidate_total_order_evaluated': False,
        'literature_panel_evaluated': False,
        'selector_evaluated': False,
        'replacement_rule_evaluated': False,
        'successor_selected': False,
        'alternative_aggregation_search': False,
        'min_max_geometric_product_search': False,
        'weight_search': False,
        'threshold_search': False,
        'top_k_search': False,
        'rank_window_search': False,
        'v31_added_to_priority_search': False,
        'boolean_combination_search': False,
        'component_size_rule_search': False,
        'graph_or_component_redefinition': False,
        'feature_search': False,
        'model_search': False,
        'k_search': False,
        'scaling_search': False,
        'diversity_search': False,
        'fusion_search': False,
        'source_quota_selected': False,
        'oracle_identity_hardcoded': False,
        'post_result_second_search': False,
        'sonotaco_role': 'EXPOSED_DEVELOPMENT_ONLY',
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (output / 'V42_JOINT_EQUAL_RANKSUM_PRIORITY_DIAGNOSTIC.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    f = sub.add_parser('freeze')
    f.add_argument('--signal-file', type=Path, required=True)
    f.add_argument('--output', type=Path, required=True)
    d = sub.add_parser('diagnose')
    d.add_argument('--freeze-file', type=Path, required=True)
    d.add_argument('--hdb-root', type=Path, required=True)
    d.add_argument('--truth-root', type=Path, required=True)
    d.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'freeze':
        return freeze_mode(a.signal_file, a.output)
    return diagnose_mode(a.freeze_file, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
