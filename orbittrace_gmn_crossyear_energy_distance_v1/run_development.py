#!/usr/bin/env python3
"""Execute the frozen GMN cross-year energy-distance representation v1.

The exact PR #1194 source is verified by Git-blob identity and executed with two
narrow insertions: one label-free scalar energy-distance table before target
construction, and one additional strict-OOF 35D evaluation after exact parent
reproduction. No parent target/model/fold/weight/diversity logic is changed.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
PARENT_ORDER_SHA = "a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592"

ANCHOR_PRETRUTH = "    req([x['key'] for x in sources] == list(MONTH_KEYS), 'GMN month sources changed')\n"
ANCHOR_POST_PARENT = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT_PRETRUTH = r'''

    # Frozen label-free representation: one empirical 4D energy-distance
    # statistic between annually centroid-aligned member distributions.
    _energy_lookup = qmod.v2.event_lookup(scan)
    _cdist = __import__('scipy.spatial.distance', fromlist=['cdist']).cdist

    def _signed_circular_delta_deg(a, b):
        return float((float(a) - float(b) + 180.0) % 360.0 - 180.0)

    def _annual_residual_matrix(_family, _year):
        _centroid = _family.get('centroids', {}).get(str(_year))
        req(_centroid is not None, f'missing frozen family centroid {_family["family_id"]} {_year}')
        _member_ids = [str(_eid) for _eid in _family['event_ids'] if int(str(_eid)[:4]) == _year]
        req(len(_member_ids) >= 1, f'empty year-member set {_family["family_id"]} {_year}')
        _rows = []
        for _eid in _member_ids:
            _event = _energy_lookup.get(_eid)
            req(_event is not None, f'member event absent from target-excluded GMN scan: {_eid}')
            _vg_event = max(abs(float(_event['vg'])), 1e-12)
            _vg_centroid = max(abs(float(_centroid['vg'])), 1e-12)
            _rows.append([
                _signed_circular_delta_deg(_event['sol'], _centroid['sol']) / 10.0,
                _signed_circular_delta_deg(_event['sun_lon'], _centroid['sun_lon']) / 4.0,
                (float(_event['ecl_lat']) - float(_centroid['ecl_lat'])) / 4.0,
                math.log(_vg_event / _vg_centroid) / math.log(1.10),
            ])
        _R = np.asarray(_rows, dtype=float)
        req(_R.ndim == 2 and _R.shape[1] == 4 and np.isfinite(_R).all(), 'invalid annual residual matrix')
        return _R

    _energy_values = []
    for _family in fams:
        _X = _annual_residual_matrix(_family, 2022)
        _Y = _annual_residual_matrix(_family, 2023)
        _xy = float(_cdist(_X, _Y, metric='euclidean').mean())
        _xx = float(_cdist(_X, _X, metric='euclidean').mean())
        _yy = float(_cdist(_Y, _Y, metric='euclidean').mean())
        _energy = 2.0 * _xy - _xx - _yy
        req(math.isfinite(_energy), 'non-finite cross-year energy distance')
        _energy_values.append(_energy)

    energy1 = np.asarray(_energy_values, dtype=float).reshape(-1, 1)
    req(energy1.shape == (4504,1) and np.isfinite(energy1).all(), f'invalid energy feature matrix {energy1.shape}')
    energy1_sha256 = array_sha(energy1)
'''

INSERT_POST_PARENT = r'''

    _parent_expected = {
        'recovered_at_25': 22,
        'recovered_at_50': 43,
        'recovered_at_100': 80,
        'recovered_at_500': 171,
        'qualified_matches': 256,
        'top100_dominant_precision': 0.8075287489258385,
        'mrr': 0.02016666446026534,
    }
    assert_metrics(share_metrics, _parent_expected, '#1194 representative-share parent')
    req(order_sha(share_order) == 'a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592', '#1194 parent order changed')
    req(x.shape == (4504,34), f'parent 34D feature matrix changed: {x.shape}')
    req(energy1.shape == (4504,1), 'energy feature shape changed')

    _x35 = np.column_stack([x, energy1])
    req(_x35.shape == (4504,35) and np.isfinite(_x35).all(), f'invalid 35D successor matrix {_x35.shape}')

    _oof_energy = np.zeros(len(ids), float)
    _fold_diag = []
    for _fold in range(5):
        _tr = folds != _fold
        _te = folds == _fold
        req(_tr.any() and _te.any(), f'empty energy fold {_fold}')
        req({groups[i] for i in np.where(_tr)[0]}.isdisjoint({groups[i] for i in np.where(_te)[0]}), f'energy group leakage fold {_fold}')
        _model = qmod.model()
        _model.fit(_x35[_tr], y_share[_tr], sample_weight=weights[_tr])
        _oof_energy[_te] = _model.predict(_x35[_te])
        _fold_diag.append({
            'fold': _fold,
            'train': int(_tr.sum()),
            'test': int(_te.sum()),
            'train_groups': len({groups[i] for i in np.where(_tr)[0]}),
            'test_groups': len({groups[i] for i in np.where(_te)[0]}),
        })
    req(np.isfinite(_oof_energy).all(), 'energy OOF prediction invalid')

    _energy_idx = qmod.diversity_order(_oof_energy, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _energy_order = [ids[i] for i in _energy_idx]
    req(len(_energy_order) == 4504 and len(set(_energy_order)) == 4504 and set(_energy_order) == set(ids), 'energy successor order changed family universe')
    _energy_metrics = qmod.v1.monotone_metrics(fams, _energy_order, truths, eligible)

    _gates = {
        'recovered_at_100_gt_80': int(_energy_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_energy_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_energy_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_energy_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_energy_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_energy_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_energy_metrics['qualified_matches']) == 256,
    }
    _passed = all(_gates.values())

    _full = {'frozen': False, 'model_sha256': None}
    if _passed:
        _full_model = qmod.model()
        _full_model.fit(_x35, y_share, sample_weight=weights)
        _full_path = a.output / 'orbittrace_gmn_crossyear_energy_distance_extratrees.joblib'
        joblib.dump(_full_model, _full_path)
        _full = {'frozen': True, 'model_sha256': sha(_full_path), 'model_class': type(_full_model).__name__}

    _result = {
        'stage': 'GMN_TARGET_EXCLUDED_CROSSYEAR_ENERGY_DISTANCE_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict': 'PASS_GMN_CROSSYEAR_ENERGY_DISTANCE_V1' if _passed else 'FAIL_GMN_CROSSYEAR_ENERGY_DISTANCE_V1',
        'candidate_counts': {'hard':226,'p19':1075,'p20':3203,'union':4504},
        'feature_dimensions': {'parent':34,'energy_added':1,'successor':35},
        'energy_definition': '2*mean_cdist_2022_2023-mean_cdist_2022_2022-mean_cdist_2023_2023',
        'energy_matrix_sha256': energy1_sha256,
        'energy_min': float(np.min(energy1)),
        'energy_median': float(np.median(energy1)),
        'energy_max': float(np.max(energy1)),
        'parent_feature_matrix_sha256': array_sha(x),
        'successor_feature_matrix_sha256': array_sha(_x35),
        'parent': trimmed(share_metrics),
        'parent_order_sha256': order_sha(share_order),
        'successor': trimmed(_energy_metrics),
        'successor_order_sha256': order_sha(_energy_order),
        'folds': _fold_diag,
        'gates': _gates,
        'full_model': _full,
        'target_changed': False,
        'folds_changed': False,
        'sample_weights_changed': False,
        'estimator_changed': False,
        'diversity_changed': False,
        'family_membership_changed': False,
        'candidate_identity_changed': False,
        'bandwidth_or_radius_used': False,
        'matching_or_transport_used': False,
        'representation_search': False,
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
    _out = a.output / 'GMN_CROSSYEAR_ENERGY_DISTANCE_V1.json'
    _out.write_text(json.dumps(_result, indent=2, sort_keys=True) + '\n')
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
    if source.count(ANCHOR_PRETRUTH) != 1:
        raise RuntimeError("pretruth energy injection anchor not unique")
    if source.count(ANCHOR_POST_PARENT) != 1:
        raise RuntimeError("post-parent energy injection anchor not unique")
    patched = source.replace(ANCHOR_PRETRUTH, ANCHOR_PRETRUTH + INSERT_PRETRUTH, 1)
    patched = patched.replace(ANCHOR_POST_PARENT, ANCHOR_POST_PARENT + INSERT_POST_PARENT, 1)
    namespace = {"__name__": "__main__", "__file__": str(parent_path), "__package__": None}
    exec(compile(patched, str(parent_path), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
