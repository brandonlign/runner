#!/usr/bin/env python3
"""Execute frozen GMN member-exclusivity margin representation v1.

Verifies and executes the exact PR #1194 source, inserting only:
  1. a label-free two-feature annual member-vs-nearest-competitor centroid
     margin table before target construction; and
  2. one strict-OOF 36D evaluation after exact #1194 parent reproduction.
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

    # Frozen label-free representation: mean annual member-event geometric
    # exclusivity against the nearest competing candidate centroid.
    _exclusive_lookup = qmod.v2.event_lookup(scan)
    _family_index = {str(_f['family_id']): _i for _i, _f in enumerate(fams)}
    req(len(_family_index) == 4504, 'family index cardinality changed')

    def _signed_circular_delta_deg(a, b):
        return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float) + 180.0) % 360.0 - 180.0

    _margin_columns = []
    _margin_hash_inputs = []
    for _year in YEARS:
        _centroids = []
        for _f in fams:
            _c = _f.get('centroids', {}).get(str(_year))
            req(_c is not None, f'missing frozen annual centroid {_f["family_id"]} {_year}')
            _vgc = max(abs(float(_c['vg'])), 1e-12)
            _centroids.append([float(_c['sol']), float(_c['sun_lon']), float(_c['ecl_lat']), math.log(_vgc)])
        _C = np.asarray(_centroids, dtype=float)
        req(_C.shape == (4504,4) and np.isfinite(_C).all(), f'invalid centroid matrix {_year}')

        # Every unique event is evaluated against the full frozen family universe
        # once; membership_map only determines which own-family margins consume
        # that event's already-computed distance vector.
        _membership_map = {}
        for _fi, _f in enumerate(fams):
            _year_members = [str(_eid) for _eid in _f['event_ids'] if int(str(_eid)[:4]) == _year]
            req(len(_year_members) >= 1, f'empty annual member set {_f["family_id"]} {_year}')
            for _eid in _year_members:
                req(_eid in _exclusive_lookup, f'member event absent from target-excluded scan: {_eid}')
                _membership_map.setdefault(_eid, []).append(_fi)
        _event_ids = sorted(_membership_map)
        req(len(_event_ids) >= 1, f'no member events {_year}')

        _sum = np.zeros(4504, dtype=float)
        _count = np.zeros(4504, dtype=np.int64)
        _batch_size = 256
        for _start in range(0, len(_event_ids), _batch_size):
            _batch_ids = _event_ids[_start:_start+_batch_size]
            _events = []
            for _eid in _batch_ids:
                _e = _exclusive_lookup[_eid]
                _vge = max(abs(float(_e['vg'])), 1e-12)
                _events.append([float(_e['sol']), float(_e['sun_lon']), float(_e['ecl_lat']), math.log(_vge)])
            _E = np.asarray(_events, dtype=float)
            req(_E.ndim == 2 and _E.shape[1] == 4 and np.isfinite(_E).all(), 'invalid event coordinate batch')

            _dsol = _signed_circular_delta_deg(_E[:,0,None], _C[None,:,0]) / 10.0
            _dlon = _signed_circular_delta_deg(_E[:,1,None], _C[None,:,1]) / 4.0
            _dlat = (_E[:,2,None] - _C[None,:,2]) / 4.0
            _dvg = (_E[:,3,None] - _C[None,:,3]) / math.log(1.10)
            _D = np.sqrt(_dsol*_dsol + _dlon*_dlon + _dlat*_dlat + _dvg*_dvg)
            req(_D.shape == (len(_batch_ids),4504) and np.isfinite(_D).all(), 'invalid event-to-centroid distance matrix')

            _nearest_idx = np.argmin(_D, axis=1)
            _two = np.partition(_D, 1, axis=1)[:,:2]
            _nearest_val = _two[:,0]
            _second_val = _two[:,1]
            for _ri, _eid in enumerate(_batch_ids):
                for _fi in _membership_map[_eid]:
                    _own = float(_D[_ri,_fi])
                    _alt = float(_second_val[_ri] if int(_nearest_idx[_ri]) == _fi else _nearest_val[_ri])
                    _margin = _alt - _own
                    req(math.isfinite(_margin), 'non-finite member exclusivity margin')
                    _sum[_fi] += _margin
                    _count[_fi] += 1

        req(np.all(_count > 0), f'missing annual exclusivity members {_year}')
        _annual = _sum / _count.astype(float)
        req(_annual.shape == (4504,) and np.isfinite(_annual).all(), f'invalid annual exclusivity feature {_year}')
        _margin_columns.append(_annual)
        _margin_hash_inputs.append({
            'year': _year,
            'unique_member_events': len(_event_ids),
            'membership_occurrences': int(_count.sum()),
            'feature_sha256': array_sha(_annual),
        })

    exclusivity2 = np.column_stack(_margin_columns)
    req(exclusivity2.shape == (4504,2) and np.isfinite(exclusivity2).all(), f'invalid exclusivity matrix {exclusivity2.shape}')
    exclusivity2_sha256 = array_sha(exclusivity2)
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
    req(x.shape == (4504,34), f'parent feature matrix changed: {x.shape}')
    req(exclusivity2.shape == (4504,2), 'exclusivity feature shape changed')

    _x36 = np.column_stack([x, exclusivity2])
    req(_x36.shape == (4504,36) and np.isfinite(_x36).all(), f'invalid 36D successor matrix {_x36.shape}')

    _oof = np.zeros(len(ids), float)
    _fold_diag = []
    for _fold in range(5):
        _tr = folds != _fold
        _te = folds == _fold
        req(_tr.any() and _te.any(), f'empty exclusivity fold {_fold}')
        req({groups[i] for i in np.where(_tr)[0]}.isdisjoint({groups[i] for i in np.where(_te)[0]}), f'exclusivity group leakage fold {_fold}')
        _model = qmod.model()
        _model.fit(_x36[_tr], y_share[_tr], sample_weight=weights[_tr])
        _oof[_te] = _model.predict(_x36[_te])
        _fold_diag.append({'fold':_fold,'train':int(_tr.sum()),'test':int(_te.sum()),'train_groups':len({groups[i] for i in np.where(_tr)[0]}),'test_groups':len({groups[i] for i in np.where(_te)[0]})})
    req(np.isfinite(_oof).all(), 'exclusivity OOF prediction invalid')

    _idx = qmod.diversity_order(_oof, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _order = [ids[i] for i in _idx]
    req(len(_order) == 4504 and len(set(_order)) == 4504 and set(_order) == set(ids), 'exclusivity successor changed family universe')
    _metrics = qmod.v1.monotone_metrics(fams, _order, truths, eligible)

    _gates = {
        'recovered_at_100_gt_80': int(_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_metrics['qualified_matches']) == 256,
    }
    _passed = all(_gates.values())

    _full = {'frozen':False,'model_sha256':None}
    if _passed:
        _full_model = qmod.model()
        _full_model.fit(_x36, y_share, sample_weight=weights)
        _full_path = a.output / 'orbittrace_gmn_member_exclusivity_margin_extratrees.joblib'
        joblib.dump(_full_model, _full_path)
        _full = {'frozen':True,'model_sha256':sha(_full_path),'model_class':type(_full_model).__name__}

    _result = {
        'stage':'GMN_TARGET_EXCLUDED_MEMBER_EXCLUSIVITY_MARGIN_V1',
        'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict':'PASS_GMN_MEMBER_EXCLUSIVITY_MARGIN_V1' if _passed else 'FAIL_GMN_MEMBER_EXCLUSIVITY_MARGIN_V1',
        'candidate_counts':{'hard':226,'p19':1075,'p20':3203,'union':4504},
        'feature_dimensions':{'parent':34,'exclusivity_added':2,'successor':36},
        'exclusivity_definition':'annual_mean(nearest_other_candidate_centroid_distance-own_candidate_centroid_distance)',
        'exclusivity_matrix_sha256':exclusivity2_sha256,
        'annual_feature_provenance':_margin_hash_inputs,
        'exclusivity_min':[float(np.min(exclusivity2[:,0])),float(np.min(exclusivity2[:,1]))],
        'exclusivity_median':[float(np.median(exclusivity2[:,0])),float(np.median(exclusivity2[:,1]))],
        'exclusivity_max':[float(np.max(exclusivity2[:,0])),float(np.max(exclusivity2[:,1]))],
        'parent_feature_matrix_sha256':array_sha(x),
        'successor_feature_matrix_sha256':array_sha(_x36),
        'parent':trimmed(share_metrics),
        'parent_order_sha256':order_sha(share_order),
        'successor':trimmed(_metrics),
        'successor_order_sha256':order_sha(_order),
        'folds':_fold_diag,
        'gates':_gates,
        'full_model':_full,
        'competitor_universe':'all_other_frozen_candidate_families_same_year',
        'nearest_k':1,
        'shared_event_competitors_excluded':False,
        'target_changed':False,
        'folds_changed':False,
        'sample_weights_changed':False,
        'estimator_changed':False,
        'diversity_changed':False,
        'family_membership_changed':False,
        'candidate_identity_changed':False,
        'threshold_search':False,
        'representation_search':False,
        'feature_selection':False,
        'post_result_second_search':False,
        'blind_exclusion':[20.0,55.0],
        'sonotaco_2013_2014_access':False,
        'sonotaco_feature_access':False,
        'target_information_access':False,
        'target_region_events_accessed':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
    }
    _out = a.output / 'GMN_MEMBER_EXCLUSIVITY_MARGIN_V1.json'
    _out.write_text(json.dumps(_result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(_result, indent=2, sort_keys=True))
'''


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1(); h.update(f"blob {len(data)}\0".encode()); h.update(data); return h.hexdigest()


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
    ns = {'__name__':'__main__','__file__':str(parent_path),'__package__':None}
    exec(compile(patched, str(parent_path), 'exec'), ns, ns)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
