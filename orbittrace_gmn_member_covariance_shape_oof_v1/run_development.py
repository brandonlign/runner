#!/usr/bin/env python3
"""Execute frozen GMN member-covariance shape OOF successor.

The exact #1194 source is verified by Git blob and executed unchanged except for
one frozen candidate-evaluation block inserted after the exact parent OOF
representative-share metrics are computed.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
PROTOCOL_GIT_BLOB = "a3d9c3aac54480ea2fb6654e1873b602ac26f60b"
PARENT_FEATURE_SHA256 = "5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1"
PARENT_TARGET_SHA256 = "4433b443030a568f9d5f6ddceab2077e9d78e50497f7ce2473bad5c113f8ab39"
PARENT_WEIGHT_SHA256 = "4ee439f0f04c9763a3dcc1527be66681496ea730df369f3c2f1815c9ef4a67f6"
PARENT_ORDER_SHA256 = "a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592"
ANCHOR = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT = r'''

    # Frozen GMN-only successor: append exactly six member-cloud second-order
    # shape descriptors. Parent target/model/folds/weights/diversity stay fixed.
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
    req(array_sha(x) == '5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1', '#1194 34D feature matrix changed')
    req(array_sha(y_share) == '4433b443030a568f9d5f6ddceab2077e9d78e50497f7ce2473bad5c113f8ab39', '#1194 representative-share target changed')
    req(array_sha(weights) == '4ee439f0f04c9763a3dcc1527be66681496ea730df369f3c2f1815c9ef4a67f6', '#1194 grouped weights changed')

    _eps = 1e-12
    _shape_names = [
        'member_shape_log_mean_scatter',
        'member_shape_mean_major_fraction',
        'member_shape_mean_spectral_entropy',
        'member_shape_scatter_balance',
        'member_shape_covariance_alignment',
        'member_shape_log_drift_to_scatter',
    ]
    _centroid_feature_index = feature_names.index('centroid_crossyear_distance')

    def _signed_circular_delta(_a, _b):
        return (float(_a) - float(_b) + 180.0) % 360.0 - 180.0

    def _year_scatter(_f, _year):
        _c = _f.get('centroids', {}).get(str(_year))
        req(_c is not None, f"missing frozen annual centroid {_f['family_id']} {_year}")
        _ids = [str(_eid) for _eid in _f['event_ids'] if int(str(_eid)[:4]) == _year]
        req(len(_ids) >= 1, f"no frozen family members {_f['family_id']} {_year}")
        _rows = []
        _cv = max(abs(float(_c['vg'])), 1e-6)
        for _eid in _ids:
            _e = lookup.get(_eid)
            req(_e is not None, f"member event absent from target-excluded GMN scan: {_eid}")
            _ev = max(abs(float(_e['vg'])), 1e-6)
            _z = [
                _signed_circular_delta(_e['sol'], _c['sol']) / 10.0,
                _signed_circular_delta(_e['sun_lon'], _c['sun_lon']) / 4.0,
                (float(_e['ecl_lat']) - float(_c['ecl_lat'])) / 4.0,
                math.log(_ev / _cv) / math.log(1.10),
            ]
            req(all(math.isfinite(_v) for _v in _z), f"nonfinite member offset {_eid}")
            _rows.append(_z)
        _z = np.asarray(_rows, dtype=float)
        _C = (_z.T @ _z) / float(len(_rows))
        req(_C.shape == (4, 4) and np.isfinite(_C).all(), f"invalid member scatter {_f['family_id']} {_year}")
        _t = float(np.trace(_C))
        req(math.isfinite(_t) and _t >= -_eps, f"invalid member scatter trace {_f['family_id']} {_year}")
        if _t < 0.0:
            _t = 0.0
        _lam = np.linalg.eigvalsh(_C)[::-1]
        _lam = np.clip(_lam, 0.0, None)
        _s = float(np.sum(_lam))
        if _s > _eps:
            _p = _lam / _s
            _nz = _p > 0.0
            _H = float(-np.sum(_p[_nz] * np.log(_p[_nz])) / math.log(4.0))
        else:
            _p = np.zeros(4, dtype=float)
            _H = 0.0
        req(np.isfinite(_p).all() and math.isfinite(_H), f"invalid member eigenspectrum {_f['family_id']} {_year}")
        return _C, _t, _p, _H

    _shape_rows = []
    for _i, _f in enumerate(fams):
        _C22, _t22, _p22, _H22 = _year_scatter(_f, 2022)
        _C23, _t23, _p23, _H23 = _year_scatter(_f, 2023)
        _mean_t = (_t22 + _t23) / 2.0
        _n22 = float(np.linalg.norm(_C22, ord='fro'))
        _n23 = float(np.linalg.norm(_C23, ord='fro'))
        _den = _n22 * _n23
        if _den > _eps:
            _align = float(np.sum(_C22 * _C23) / _den)
            _align = float(np.clip(_align, 0.0, 1.0))
        else:
            _align = 0.0
        _dcent = float(x[_i, _centroid_feature_index])
        _row = [
            math.log1p(_mean_t),
            float((_p22[0] + _p23[0]) / 2.0),
            float((_H22 + _H23) / 2.0),
            float((min(_t22, _t23) + _eps) / (max(_t22, _t23) + _eps)),
            _align,
            math.log1p(_dcent / math.sqrt(_mean_t + _eps)),
        ]
        req(len(_row) == 6 and all(math.isfinite(_v) for _v in _row), f"invalid shape feature row {_f['family_id']}")
        _shape_rows.append(_row)

    _shape = np.asarray(_shape_rows, dtype=float)
    req(_shape.shape == (4504, 6) and np.isfinite(_shape).all(), f"invalid frozen shape block {_shape.shape}")
    _x40 = np.column_stack([x, _shape])
    req(_x40.shape == (4504, 40) and np.isfinite(_x40).all(), f"invalid 40D candidate feature matrix {_x40.shape}")

    _oof40 = np.zeros(len(ids), dtype=float)
    for _fold in range(5):
        _tr = folds != _fold
        _te = folds == _fold
        req(_tr.any() and _te.any(), f"empty member-covariance fold {_fold}")
        req({groups[_j] for _j in np.where(_tr)[0]}.isdisjoint({groups[_j] for _j in np.where(_te)[0]}), f"member-covariance group leakage fold {_fold}")
        _m = qmod.model()
        _m.fit(_x40[_tr], y_share[_tr], sample_weight=weights[_tr])
        _oof40[_te] = _m.predict(_x40[_te])
    req(np.isfinite(_oof40).all(), 'member-covariance OOF prediction invalid')

    _idx40 = qmod.diversity_order(_oof40, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _order40 = [ids[_i] for _i in _idx40]
    req(len(_order40) == 4504 and len(set(_order40)) == 4504, 'member-covariance order universe changed')
    _metrics40 = qmod.v1.monotone_metrics(fams, _order40, truths, eligible)

    _gates = {
        'recovered_at_100_gt_80': int(_metrics40['recovered_at_100']) > 80,
        'recovered_at_25_ge_22': int(_metrics40['recovered_at_25']) >= 22,
        'recovered_at_50_ge_43': int(_metrics40['recovered_at_50']) >= 43,
        'recovered_at_500_ge_171': int(_metrics40['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_metrics40['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_metrics40['mrr']) >= 0.02016666446026534,
        'qualified_eq_256': int(_metrics40['qualified_matches']) == 256,
    }
    _passed40 = bool(all(_gates.values()))
    _result40 = {
        'stage': 'GMN_TARGET_EXCLUDED_MEMBER_COVARIANCE_SHAPE_OOF_V1',
        'verdict': 'PASS_GMN_MEMBER_COVARIANCE_SHAPE_OOF_V1' if _passed40 else 'FAIL_GMN_MEMBER_COVARIANCE_SHAPE_OOF_V1',
        'scientific_role': 'GMN_2022_2023_TARGET_EXCLUDED_METHOD_DEVELOPMENT_ONLY',
        'sole_scientific_change': 'append the six protocol-frozen within-family member-cloud second-order shape descriptors to exact #1194 34D representation; target/model/folds/weights/diversity/evaluator unchanged',
        'candidate_counts': {'hard': 226, 'p19': 1075, 'p20': 3203, 'union': 4504},
        'feature_dimension_parent': 34,
        'feature_dimension_candidate': 40,
        'shape_feature_names': _shape_names,
        'parent_feature_sha256': array_sha(x),
        'shape_block_sha256': array_sha(_shape),
        'candidate_feature_sha256': array_sha(_x40),
        'representative_share_target_sha256': array_sha(y_share),
        'grouped_weights_sha256': array_sha(weights),
        'parent_oof': trimmed(share_metrics),
        'parent_oof_order_sha256': order_sha(share_order),
        'candidate_oof': trimmed(_metrics40),
        'candidate_oof_order_sha256': order_sha(_order40),
        'binding_gates': _gates,
        'all_binding_gates_pass': _passed40,
        'model': 'exact #1194 ExtraTreesRegressor',
        'diversity': dict(DIVERSITY),
        'full_candidate_model_fit': False,
        'candidate_generation_recomputed': False,
        'membership_changed': False,
        'same_shower_all_fragments_same_fold': True,
        'development_truth_used_for_training': True,
        'feature_search': False,
        'model_search': False,
        'hyperparameter_search': False,
        'diversity_search': False,
        'target_search': False,
        'sonotaco_2013_2014_access': False,
        'sonotaco_feature_access': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'blind_exclusion': [20.0, 55.0],
    }
    (a.output / 'GMN_MEMBER_COVARIANCE_SHAPE_OOF_V1.json').write_text(
        json.dumps(_result40, indent=2, sort_keys=True, allow_nan=False) + '\n'
    )
    print(json.dumps(_result40, indent=2, sort_keys=True, allow_nan=False))
'''


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def main() -> int:
    parent_path = Path(os.environ["ORBITTRACE_REPRESENTATIVE_SHARE_PARENT_SOURCE"])
    protocol_path = Path(__file__).with_name("PROTOCOL.md")
    if not parent_path.is_file():
        raise RuntimeError(f"missing exact #1194 parent source: {parent_path}")
    if git_blob_sha(protocol_path.read_bytes()) != PROTOCOL_GIT_BLOB:
        raise RuntimeError("frozen member-covariance protocol changed")
    data = parent_path.read_bytes()
    if git_blob_sha(data) != PARENT_GIT_BLOB:
        raise RuntimeError("exact #1194 parent Git blob changed")
    source = data.decode("utf-8")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("#1194 member-covariance injection anchor not unique")
    patched = source.replace(ANCHOR, ANCHOR + INSERT, 1)
    namespace = {"__name__": "__main__", "__file__": str(parent_path), "__package__": None}
    exec(compile(patched, str(parent_path), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
