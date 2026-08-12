#!/usr/bin/env python3
"""Execute the frozen GMN member-instance pooled-regression v1 successor.

The exact #1194 source is verified byte-for-byte and used as the scientific
parent. This wrapper inserts only:
  1. the preregistered label-free 4D member-residual table before truth use;
  2. the preregistered strict-OOF instance regression after exact parent
     reproduction.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
PARENT_ORDER_SHA = "a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592"
EXPECTED_INSTANCE_ROWS = 74497

ANCHOR_PRETRUTH = "    req([x['key'] for x in sources] == list(MONTH_KEYS), 'GMN month sources changed')\n"
ANCHOR_POST_PARENT = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT_PRETRUTH = r'''

    # Frozen pretruth member-instance representation. Construct only from the
    # target-excluded event scan, immutable family memberships and immutable
    # annual family centroids. No truth/target is available at this point.
    _mi_lookup = qmod.v2.event_lookup(scan)

    def _mi_signed_circular_delta_deg(_a, _b):
        return (float(_a) - float(_b) + 180.0) % 360.0 - 180.0

    _mi_family_index_list = []
    _mi_event_ids = []
    _mi_residual_rows = []
    _mi_year_counts = {2022: 0, 2023: 0}
    for _fi, _f in enumerate(fams):
        _fid = str(_f['family_id'])
        _eids = [str(_eid) for _eid in _f['event_ids']]
        req(len(_eids) == len(set(_eids)), f'duplicate member ID within family {_fid}')
        req(len(_eids) >= 2, f'family has fewer than two total members {_fid}')
        for _eid in _eids:
            req(_eid in _mi_lookup, f'member event absent from target-excluded scan: {_eid}')
            _year = int(_eid[:4])
            req(_year in YEARS, f'member year outside frozen panel: {_eid}')
            _c = _f.get('centroids', {}).get(str(_year))
            req(_c is not None, f'missing annual centroid {_fid} {_year}')
            _e = _mi_lookup[_eid]
            _vge = max(abs(float(_e['vg'])), 1e-12)
            _vgc = max(abs(float(_c['vg'])), 1e-12)
            _row = [
                _mi_signed_circular_delta_deg(_e['sol'], _c['sol']) / 10.0,
                _mi_signed_circular_delta_deg(_e['sun_lon'], _c['sun_lon']) / 4.0,
                (float(_e['ecl_lat']) - float(_c['ecl_lat'])) / 4.0,
                math.log(_vge / _vgc) / math.log(1.10),
            ]
            req(all(math.isfinite(float(_z)) for _z in _row), f'nonfinite member residual {_fid} {_eid}')
            _mi_family_index_list.append(_fi)
            _mi_event_ids.append(_eid)
            _mi_residual_rows.append(_row)
            _mi_year_counts[_year] += 1

    _mi_family_index = np.asarray(_mi_family_index_list, dtype=np.int64)
    _mi_residual4 = np.asarray(_mi_residual_rows, dtype=float)
    req(len(_mi_event_ids) == 74497, f'member-occurrence count changed: {len(_mi_event_ids)}')
    req(_mi_family_index.shape == (74497,), f'family-index shape changed: {_mi_family_index.shape}')
    req(_mi_residual4.shape == (74497,4) and np.isfinite(_mi_residual4).all(), f'invalid pretruth residual matrix {_mi_residual4.shape}')
    req(int(np.min(_mi_family_index)) == 0 and int(np.max(_mi_family_index)) == 4503, 'member family-index support changed')
    _mi_occurrence_counts = np.bincount(_mi_family_index, minlength=4504)
    req(_mi_occurrence_counts.shape == (4504,) and np.all(_mi_occurrence_counts > 0), 'family missing member occurrences')
    _mi_residual4_sha256 = array_sha(_mi_residual4)
    _mi_membership_key_sha256 = hashlib.sha256(
        '\n'.join(f'{int(_fi)}\t{_eid}' for _fi, _eid in zip(_mi_family_index_list, _mi_event_ids)).encode()
    ).hexdigest()
'''

INSERT_POST_PARENT = r'''

    # Binding interpretation starts only after exact #1194 reproduction.
    _mi_parent_expected = {
        'recovered_at_25': 22,
        'recovered_at_50': 43,
        'recovered_at_100': 80,
        'recovered_at_500': 171,
        'qualified_matches': 256,
        'top100_dominant_precision': 0.8075287489258385,
        'mrr': 0.02016666446026534,
    }
    assert_metrics(share_metrics, _mi_parent_expected, '#1194 representative-share parent')
    req(order_sha(share_order) == 'a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592', '#1194 parent order changed')
    req(x.shape == (4504,34) and np.isfinite(x).all(), f'parent feature matrix changed: {x.shape}')
    req(_mi_residual4.shape == (74497,4), 'pretruth residual shape changed')

    # The sole 38D instance representation: exact 34D family context plus the
    # current member occurrence's four signed normalized residuals.
    _mi_x38 = np.column_stack([x[_mi_family_index], _mi_residual4])
    req(_mi_x38.shape == (74497,38) and np.isfinite(_mi_x38).all(), f'invalid instance matrix {_mi_x38.shape}')
    _mi_x38_sha256 = array_sha(_mi_x38)

    _mi_oof = np.full(len(ids), np.nan, dtype=float)
    _mi_fold_diag = []
    _mi_max_weight_error = 0.0

    for _fold in range(5):
        _test_family = folds == _fold
        _train_family = folds != _fold
        req(_test_family.any() and _train_family.any(), f'empty family fold {_fold}')
        req({groups[i] for i in np.where(_train_family)[0]}.isdisjoint({groups[i] for i in np.where(_test_family)[0]}), f'whole-shower group leakage fold {_fold}')

        _test_row = _test_family[_mi_family_index]
        _candidate_train_row = _train_family[_mi_family_index]
        req(bool(np.any(_test_row)) and bool(np.any(_candidate_train_row)), f'empty instance split fold {_fold}')

        _test_events = {_mi_event_ids[_ri] for _ri in np.where(_test_row)[0]}
        _purge_mask = np.asarray([_eid in _test_events for _eid in _mi_event_ids], dtype=bool)
        _train_row = _candidate_train_row & (~_purge_mask)
        req(bool(np.any(_train_row)), f'all training rows purged fold {_fold}')

        _train_event_set = {_mi_event_ids[_ri] for _ri in np.where(_train_row)[0]}
        req(_train_event_set.isdisjoint(_test_events), f'event-ID leakage after purge fold {_fold}')

        _retained_counts = np.bincount(_mi_family_index[_train_row], minlength=4504)
        _train_family_indices = np.where(_train_family)[0]
        req(np.all(_retained_counts[_train_family_indices] > 0), f'training family emptied by event purge fold {_fold}')
        req(np.all(_retained_counts[np.where(_test_family)[0]] == 0), f'test family leaked into train rows fold {_fold}')

        _row_fi = _mi_family_index[_train_row]
        _row_weights = weights[_row_fi] / _retained_counts[_row_fi]
        req(np.isfinite(_row_weights).all() and np.all(_row_weights > 0.0), f'invalid row weights fold {_fold}')
        _weight_sums = np.bincount(_row_fi, weights=_row_weights, minlength=4504)
        _weight_error = float(np.max(np.abs(_weight_sums[_train_family_indices] - weights[_train_family_indices])))
        _mi_max_weight_error = max(_mi_max_weight_error, _weight_error)
        req(_weight_error < 1e-12, f'family weight conservation failed fold {_fold}: {_weight_error}')

        _row_target = y_share[_row_fi]
        req(np.isfinite(_row_target).all(), f'invalid repeated family targets fold {_fold}')

        _model = qmod.model()
        _model.fit(_mi_x38[_train_row], _row_target, sample_weight=_row_weights)

        _test_rows_idx = np.where(_test_row)[0]
        _pred = np.asarray(_model.predict(_mi_x38[_test_row]), dtype=float)
        req(_pred.shape == (len(_test_rows_idx),) and np.isfinite(_pred).all(), f'invalid instance predictions fold {_fold}')
        _test_fi = _mi_family_index[_test_row]
        _pred_sum = np.bincount(_test_fi, weights=_pred, minlength=4504)
        _pred_count = np.bincount(_test_fi, minlength=4504)
        _test_family_indices = np.where(_test_family)[0]
        req(np.all(_pred_count[_test_family_indices] > 0), f'held-out family missing predictions fold {_fold}')
        _mi_oof[_test_family_indices] = _pred_sum[_test_family_indices] / _pred_count[_test_family_indices]

        _mi_fold_diag.append({
            'fold': _fold,
            'train_families': int(_train_family.sum()),
            'test_families': int(_test_family.sum()),
            'candidate_train_rows': int(_candidate_train_row.sum()),
            'retained_train_rows': int(_train_row.sum()),
            'purged_train_rows': int(_candidate_train_row.sum() - _train_row.sum()),
            'test_rows': int(_test_row.sum()),
            'unique_train_events_after_purge': len(_train_event_set),
            'unique_test_events': len(_test_events),
            'event_id_overlap_after_purge': 0,
            'minimum_retained_rows_per_training_family': int(np.min(_retained_counts[_train_family_indices])),
            'maximum_family_weight_conservation_error': _weight_error,
        })

    req(_mi_oof.shape == (4504,) and np.isfinite(_mi_oof).all(), 'member-instance OOF family scores incomplete')

    _mi_idx = qmod.diversity_order(_mi_oof, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _mi_order = [ids[i] for i in _mi_idx]
    req(len(_mi_order) == 4504 and len(set(_mi_order)) == 4504 and set(_mi_order) == set(ids), 'member-instance successor changed family universe')
    _mi_metrics = qmod.v1.monotone_metrics(fams, _mi_order, truths, eligible)

    _mi_gates = {
        'recovered_at_100_gt_80': int(_mi_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_mi_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_mi_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_mi_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_mi_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_mi_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_mi_metrics['qualified_matches']) == 256,
    }
    _mi_passed = all(_mi_gates.values())

    _mi_full = {'frozen': False, 'model_sha256': None}
    if _mi_passed:
        _full_counts = np.bincount(_mi_family_index, minlength=4504)
        req(np.all(_full_counts > 0), 'full-fit family missing instances')
        _full_weights = weights[_mi_family_index] / _full_counts[_mi_family_index]
        _full_weight_sums = np.bincount(_mi_family_index, weights=_full_weights, minlength=4504)
        req(float(np.max(np.abs(_full_weight_sums - weights))) < 1e-12, 'full-fit family weights not conserved')
        _full_targets = y_share[_mi_family_index]
        _full_model = qmod.model()
        _full_model.fit(_mi_x38, _full_targets, sample_weight=_full_weights)
        _full_path = a.output / 'orbittrace_gmn_member_instance_pooled_regression_extratrees.joblib'
        joblib.dump(_full_model, _full_path)
        _mi_full = {
            'frozen': True,
            'model_class': type(_full_model).__name__,
            'model_sha256': sha(_full_path),
            'pooling': 'unweighted_arithmetic_mean_over_all_family_member_occurrences',
        }

    _mi_result = {
        'stage': 'GMN_TARGET_EXCLUDED_MEMBER_INSTANCE_POOLED_REGRESSION_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict': 'PASS_GMN_MEMBER_INSTANCE_POOLED_REGRESSION_V1' if _mi_passed else 'FAIL_GMN_MEMBER_INSTANCE_POOLED_REGRESSION_V1',
        'candidate_counts': {'hard':226,'p19':1075,'p20':3203,'union':4504},
        'feature_dimensions': {'family_context':34,'member_residual':4,'instance':38},
        'instance_row_count': int(len(_mi_event_ids)),
        'year_instance_counts': {str(_y): int(_mi_year_counts[_y]) for _y in YEARS},
        'member_residual_matrix_sha256': _mi_residual4_sha256,
        'member_occurrence_key_sha256': _mi_membership_key_sha256,
        'instance_matrix_sha256': _mi_x38_sha256,
        'parent_feature_matrix_sha256': array_sha(x),
        'parent': trimmed(share_metrics),
        'parent_order_sha256': order_sha(share_order),
        'successor': trimmed(_mi_metrics),
        'successor_order_sha256': order_sha(_mi_order),
        'gates': _mi_gates,
        'folds': _mi_fold_diag,
        'maximum_family_weight_conservation_error': _mi_max_weight_error,
        'family_score_pooling': 'unweighted_arithmetic_mean_all_member_occurrences_both_years',
        'event_id_purge_rule': 'remove_training_instance_if_event_id_occurs_in_any_test_family',
        'full_model': _mi_full,
        'target_changed': False,
        'family_folds_changed': False,
        'family_total_weights_changed': False,
        'estimator_changed': False,
        'diversity_changed': False,
        'family_membership_changed': False,
        'candidate_identity_changed': False,
        'competitor_features_used': False,
        'background_features_used': False,
        'orbital_features_used': False,
        'uncertainty_features_used': False,
        'pooling_search': False,
        'model_hyperparameter_search': False,
        'feature_selection': False,
        'post_result_second_search': False,
        'blind_exclusion': [20.0,55.0],
        'sonotaco_2013_2014_access': False,
        'sonotaco_feature_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    _mi_out = a.output / 'GMN_MEMBER_INSTANCE_POOLED_REGRESSION_V1.json'
    _mi_out.write_text(json.dumps(_mi_result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(_mi_result, indent=2, sort_keys=True))
'''


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def main() -> int:
    parent_path = Path(os.environ['ORBITTRACE_REPRESENTATIVE_SHARE_PARENT_SOURCE'])
    if not parent_path.is_file():
        raise RuntimeError(f'missing exact #1194 parent source: {parent_path}')
    data = parent_path.read_bytes()
    if git_blob_sha(data) != PARENT_GIT_BLOB:
        raise RuntimeError('exact #1194 parent Git blob changed')
    source = data.decode('utf-8')
    if source.count(ANCHOR_PRETRUTH) != 1 or source.count(ANCHOR_POST_PARENT) != 1:
        raise RuntimeError('frozen injection anchor changed')
    patched = source.replace(ANCHOR_PRETRUTH, ANCHOR_PRETRUTH + INSERT_PRETRUTH, 1)
    patched = patched.replace(ANCHOR_POST_PARENT, ANCHOR_POST_PARENT + INSERT_POST_PARENT, 1)
    namespace = {'__name__':'__main__','__file__':str(parent_path),'__package__':None}
    exec(compile(patched, str(parent_path), 'exec'), namespace, namespace)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
