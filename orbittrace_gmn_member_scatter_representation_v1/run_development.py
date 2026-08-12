#!/usr/bin/env python3
"""Execute the frozen GMN member-scatter representation v1 successor.

The exact PR #1194 scientific source is verified by Git-blob identity and then
executed with two narrow insertions:
  1. compute the preregistered label-free 20D per-year physical residual
     second-moment representation before target construction; and
  2. evaluate exactly one additional strict-OOF model using [34D parent + 20D]
     after the exact #1194 parent order has been reproduced.

No parent target, fold, sample weight, estimator, diversity parameter, family
membership, or candidate identity is changed.
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

    # Frozen label-free representation. This block uses only family memberships,
    # family centroids, and target-excluded GMN event coordinates. It is executed
    # before eligible-label / family-truth / target construction below.
    _scatter_lookup = qmod.v2.event_lookup(scan)

    def _signed_circular_delta_deg(a, b):
        return float((float(a) - float(b) + 180.0) % 360.0 - 180.0)

    _scatter_rows = []
    _scatter_feature_names = []
    _upper = ((0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3),(2,2),(2,3),(3,3))
    for _year in YEARS:
        for _u, _v in _upper:
            _scatter_feature_names.append(f'member_scatter_{_year}_{_u}{_v}')

    for _family in fams:
        _row_features = []
        _centroids = _family.get('centroids', {})
        for _year in YEARS:
            _centroid = _centroids.get(str(_year))
            req(_centroid is not None, f'missing frozen family centroid {_family["family_id"]} {_year}')
            _member_ids = [str(_eid) for _eid in _family['event_ids'] if int(str(_eid)[:4]) == _year]
            req(len(_member_ids) >= 1, f'empty year-member set {_family["family_id"]} {_year}')
            _residuals = []
            for _eid in _member_ids:
                _event = _scatter_lookup.get(_eid)
                req(_event is not None, f'member event absent from target-excluded GMN scan: {_eid}')
                _vg_event = max(abs(float(_event['vg'])), 1e-12)
                _vg_centroid = max(abs(float(_centroid['vg'])), 1e-12)
                _residuals.append([
                    _signed_circular_delta_deg(_event['sol'], _centroid['sol']) / 10.0,
                    _signed_circular_delta_deg(_event['sun_lon'], _centroid['sun_lon']) / 4.0,
                    (float(_event['ecl_lat']) - float(_centroid['ecl_lat'])) / 4.0,
                    math.log(_vg_event / _vg_centroid) / math.log(1.10),
                ])
            _R = np.asarray(_residuals, dtype=float)
            req(_R.ndim == 2 and _R.shape[1] == 4 and np.isfinite(_R).all(), 'invalid member residual matrix')
            _S = (_R.T @ _R) / float(len(_R))
            req(_S.shape == (4,4) and np.isfinite(_S).all(), 'invalid member second-moment tensor')
            _row_features.extend(float(_S[_u,_v]) for _u,_v in _upper)
        req(len(_row_features) == 20 and all(math.isfinite(_x) for _x in _row_features), 'invalid 20D member-scatter row')
        _scatter_rows.append(_row_features)

    scatter20 = np.asarray(_scatter_rows, dtype=float)
    req(scatter20.shape == (4504,20) and np.isfinite(scatter20).all(), f'invalid member-scatter matrix {scatter20.shape}')
    scatter20_sha256 = array_sha(scatter20)
    req(len(_scatter_feature_names) == 20 and len(set(_scatter_feature_names)) == 20, 'scatter feature schema changed')
'''

INSERT_POST_PARENT = r'''

    # Exact #1194 parent must reproduce before successor interpretation.
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
    req(scatter20.shape == (4504,20), 'scatter representation shape changed')

    _x54 = np.column_stack([x, scatter20])
    req(_x54.shape == (4504,54) and np.isfinite(_x54).all(), f'invalid 54D successor matrix {_x54.shape}')

    _oof_scatter = np.zeros(len(ids), float)
    _scatter_fold_diag = []
    for _fold in range(5):
        _tr = folds != _fold
        _te = folds == _fold
        req(_tr.any() and _te.any(), f'empty member-scatter fold {_fold}')
        req({groups[i] for i in np.where(_tr)[0]}.isdisjoint({groups[i] for i in np.where(_te)[0]}), f'member-scatter group leakage fold {_fold}')
        _model = qmod.model()
        _model.fit(_x54[_tr], y_share[_tr], sample_weight=weights[_tr])
        _oof_scatter[_te] = _model.predict(_x54[_te])
        _scatter_fold_diag.append({
            'fold': _fold,
            'train': int(_tr.sum()),
            'test': int(_te.sum()),
            'train_groups': len({groups[i] for i in np.where(_tr)[0]}),
            'test_groups': len({groups[i] for i in np.where(_te)[0]}),
        })
    req(np.isfinite(_oof_scatter).all(), 'member-scatter OOF prediction invalid')

    _scatter_idx = qmod.diversity_order(_oof_scatter, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _scatter_order = [ids[i] for i in _scatter_idx]
    req(len(_scatter_order) == 4504 and len(set(_scatter_order)) == 4504 and set(_scatter_order) == set(ids), 'successor order changed family universe')
    _scatter_metrics = qmod.v1.monotone_metrics(fams, _scatter_order, truths, eligible)

    _gates = {
        'recovered_at_100_gt_80': int(_scatter_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_scatter_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_scatter_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_scatter_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_scatter_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_scatter_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_scatter_metrics['qualified_matches']) == 256,
    }
    _passed = all(_gates.values())

    _full = {'frozen': False, 'model_sha256': None}
    if _passed:
        _full_model = qmod.model()
        _full_model.fit(_x54, y_share, sample_weight=weights)
        _full_path = a.output / 'orbittrace_gmn_member_scatter_representative_share_extratrees.joblib'
        joblib.dump(_full_model, _full_path)
        _full = {
            'frozen': True,
            'model_sha256': sha(_full_path),
            'model_class': type(_full_model).__name__,
        }

    _result = {
        'stage': 'GMN_TARGET_EXCLUDED_MEMBER_SCATTER_REPRESENTATION_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict': 'PASS_GMN_MEMBER_SCATTER_REPRESENTATION_V1' if _passed else 'FAIL_GMN_MEMBER_SCATTER_REPRESENTATION_V1',
        'candidate_counts': {'hard':226,'p19':1075,'p20':3203,'union':4504},
        'feature_dimensions': {'parent':34,'scatter_added':20,'successor':54},
        'scatter_feature_names': list(_scatter_feature_names),
        'scatter_matrix_sha256': scatter20_sha256,
        'parent_feature_matrix_sha256': array_sha(x),
        'successor_feature_matrix_sha256': array_sha(_x54),
        'parent': trimmed(share_metrics),
        'parent_order_sha256': order_sha(share_order),
        'successor': trimmed(_scatter_metrics),
        'successor_order_sha256': order_sha(_scatter_order),
        'folds': _scatter_fold_diag,
        'gates': _gates,
        'full_model': _full,
        'target_changed': False,
        'folds_changed': False,
        'sample_weights_changed': False,
        'estimator_changed': False,
        'diversity_changed': False,
        'family_membership_changed': False,
        'candidate_identity_changed': False,
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
    _out = a.output / 'GMN_MEMBER_SCATTER_REPRESENTATION_V1.json'
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
        raise RuntimeError("pretruth representation injection anchor not unique")
    if source.count(ANCHOR_POST_PARENT) != 1:
        raise RuntimeError("post-parent evaluation injection anchor not unique")
    patched = source.replace(ANCHOR_PRETRUTH, ANCHOR_PRETRUTH + INSERT_PRETRUTH, 1)
    patched = patched.replace(ANCHOR_POST_PARENT, ANCHOR_POST_PARENT + INSERT_POST_PARENT, 1)
    namespace = {"__name__": "__main__", "__file__": str(parent_path), "__package__": None}
    exec(compile(patched, str(parent_path), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
