#!/usr/bin/env python3
"""Execute the frozen #1194 representative-share oracle diagnostic.

The exact #1194 source is verified by Git blob and executed unchanged except for
one diagnostic block inserted immediately after its OOF representative-share
metrics are computed. The inserted block fits no model and searches no rule.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
PARENT_ORDER_SHA = "a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592"
ANCHOR = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT = r'''

    # Frozen diagnostic only: evaluate the two pre-existing truth target vectors
    # as oracle scores under the exact unchanged diversity operator.
    _parent_expected = {
        'recovered_at_25': 22,
        'recovered_at_50': 43,
        'recovered_at_100': 80,
        'recovered_at_500': 171,
        'qualified_matches': 256,
        'top100_dominant_precision': 0.8075287489258385,
        'mrr': 0.02016666446026534,
    }
    assert_metrics(share_metrics, _parent_expected, '#1194 representative-share OOF parent')
    req(order_sha(share_order) == 'a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592', '#1194 OOF order changed')
    req(len(share_order) == 4504 and len(set(share_order)) == 4504, '#1194 order universe changed')

    _oracle_share_idx = qmod.diversity_order(y_share, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _oracle_share_order = [ids[i] for i in _oracle_share_idx]
    _oracle_share_metrics = qmod.v1.monotone_metrics(fams, _oracle_share_order, truths, eligible)

    _oracle_abs_idx = qmod.diversity_order(q_abs, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _oracle_abs_order = [ids[i] for i in _oracle_abs_idx]
    _oracle_abs_metrics = qmod.v1.monotone_metrics(fams, _oracle_abs_order, truths, eligible)

    req(len(_oracle_share_order) == 4504 and len(set(_oracle_share_order)) == 4504, 'share oracle universe changed')
    req(len(_oracle_abs_order) == 4504 and len(set(_oracle_abs_order)) == 4504, 'absolute oracle universe changed')
    req(set(_oracle_share_order) == set(share_order) == set(_oracle_abs_order), 'oracle candidate identity set changed')

    def _labels_at_100(metrics):
        return {
            str(label)
            for label, rank in metrics['first_rank_by_label'].items()
            if int(rank) <= 100
        }

    _parent_labels = _labels_at_100(share_metrics)
    _share_labels = _labels_at_100(_oracle_share_metrics)
    _abs_labels = _labels_at_100(_oracle_abs_metrics)
    req(len(_parent_labels) == int(share_metrics['recovered_at_100']), 'parent label-set count mismatch')
    req(len(_share_labels) == int(_oracle_share_metrics['recovered_at_100']), 'share oracle label-set count mismatch')
    req(len(_abs_labels) == int(_oracle_abs_metrics['recovered_at_100']), 'absolute oracle label-set count mismatch')

    _parent_top100_ids = set(share_order[:100])
    _share_top100_ids = set(_oracle_share_order[:100])

    _result = {
        'stage': 'GMN_TARGET_EXCLUDED_REPRESENTATIVE_SHARE_ORACLE_DIAGNOSTIC_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_DIAGNOSTIC_ONLY',
        'candidate_counts': {'hard': 226, 'p19': 1075, 'p20': 3203, 'union': 4504},
        'eligible_recurrent_labels': len(eligible),
        'qualified_matches': int(share_metrics['qualified_matches']),
        'diversity': dict(DIVERSITY),
        'parent_oof': trimmed(share_metrics),
        'parent_oof_order_sha256': order_sha(share_order),
        'representative_share_oracle': trimmed(_oracle_share_metrics),
        'representative_share_oracle_order_sha256': order_sha(_oracle_share_order),
        'absolute_quality_oracle': trimmed(_oracle_abs_metrics),
        'absolute_quality_oracle_order_sha256': order_sha(_oracle_abs_order),
        'top100_comparison': {
            'parent_distinct_qualified_labels': len(_parent_labels),
            'representative_share_oracle_distinct_qualified_labels': len(_share_labels),
            'absolute_quality_oracle_distinct_qualified_labels': len(_abs_labels),
            'parent_share_oracle_family_id_overlap': len(_parent_top100_ids & _share_top100_ids),
            'parent_share_oracle_label_overlap': len(_parent_labels & _share_labels),
            'share_oracle_only_labels': len(_share_labels - _parent_labels),
            'parent_only_labels': len(_parent_labels - _share_labels),
        },
        'representative_share_oracle_improves_at_100': int(_oracle_share_metrics['recovered_at_100']) > 80,
        'representative_share_oracle_reaches_known_100_at_100_ceiling': int(_oracle_share_metrics['recovered_at_100']) == 100,
        'no_model_fit_for_oracles': True,
        'no_target_search': True,
        'no_diversity_search': True,
        'no_threshold_search': True,
        'no_successor_selected': True,
        'blind_exclusion': [20.0, 55.0],
        'sonotaco_2013_2014_access': False,
        'sonotaco_feature_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    _oracle_output = a.output / 'GMN_REPRESENTATIVE_SHARE_ORACLE_DIAGNOSTIC_V1.json'
    _oracle_output.write_text(json.dumps(_result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(_result, indent=2, sort_keys=True))
'''


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def main() -> int:
    parent_path = Path(os.environ["ORBITTRACE_REPRESENTATIVE_SHARE_PARENT_SOURCE"])
    if not parent_path.is_file():
        raise RuntimeError(f"missing exact #1194 parent source: {parent_path}")
    data = parent_path.read_bytes()
    if git_blob_sha(data) != PARENT_GIT_BLOB:
        raise RuntimeError("exact #1194 parent Git blob changed")
    source = data.decode("utf-8")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("#1194 diagnostic injection anchor not unique")
    patched = source.replace(ANCHOR, ANCHOR + INSERT, 1)
    namespace = {"__name__": "__main__", "__file__": str(parent_path), "__package__": None}
    exec(compile(patched, str(parent_path), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
