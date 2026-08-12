#!/usr/bin/env python3
"""Execute frozen GMN member-cloud MST bottleneck topology v1."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
ANCHOR_PRETRUTH = "    req([x['key'] for x in sources] == list(MONTH_KEYS), 'GMN month sources changed')\n"
ANCHOR_POST_PARENT = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT_PRETRUTH = r'''

    # Frozen label-free annual member-cloud topology, built before truth/target use.
    _mst_lookup = qmod.v2.event_lookup(scan)

    def _mst_signed_circular_delta_deg(_a, _b):
        return (float(_a) - float(_b) + 180.0) % 360.0 - 180.0

    def _mst_bottleneck_share(_rows):
        _r = np.asarray(_rows, dtype=float)
        req(_r.ndim == 2 and _r.shape[1] == 4 and len(_r) >= 1 and np.isfinite(_r).all(), 'invalid MST residual cloud')
        _n = len(_r)
        if _n == 1:
            return 0.0
        _delta = _r[:,None,:] - _r[None,:,:]
        _D = np.sqrt(np.sum(_delta*_delta, axis=2))
        req(_D.shape == (_n,_n) and np.isfinite(_D).all(), 'invalid MST pairwise distances')
        req(float(np.max(np.abs(_D-_D.T))) < 1e-12, 'MST distance matrix asymmetric')
        _visited = np.zeros(_n, dtype=bool)
        _visited[0] = True
        _best = _D[0].copy()
        _best[0] = np.inf
        _edges = []
        for _step in range(1, _n):
            _candidates = np.where(~_visited)[0]
            req(len(_candidates) >= 1, 'MST candidate set unexpectedly empty')
            # np.argmin over ascending candidate indices gives the frozen smallest-index tie rule.
            _local = int(np.argmin(_best[_candidates]))
            _j = int(_candidates[_local])
            _edge = float(_best[_j])
            req(math.isfinite(_edge) and _edge >= 0.0, 'invalid MST selected edge')
            _edges.append(_edge)
            _visited[_j] = True
            _remaining = np.where(~_visited)[0]
            for _k in _remaining:
                _d = float(_D[_j, _k])
                if _d < float(_best[_k]):
                    _best[_k] = _d
        req(bool(np.all(_visited)) and len(_edges) == _n-1, 'MST construction incomplete')
        _total = float(sum(_edges))
        if _total == 0.0:
            return 0.0
        _value = float(max(_edges) / _total)
        req(math.isfinite(_value) and -1e-15 <= _value <= 1.0+1e-15, 'MST bottleneck share outside range')
        return min(max(_value, 0.0), 1.0)

    _mst_columns = []
    _mst_year_meta = []
    _mst_total_occurrences = 0
    for _year in YEARS:
        _values = np.empty(len(fams), dtype=float)
        _year_occurrences = 0
        _singleton_families = 0
        _zero_total_families = 0
        for _fi, _f in enumerate(fams):
            _fid = str(_f['family_id'])
            _ids = sorted(str(_eid) for _eid in _f['event_ids'] if int(str(_eid)[:4]) == _year)
            req(len(_ids) >= 1, f'empty annual member set {_fid} {_year}')
            req(len(_ids) == len(set(_ids)), f'duplicate annual member ID {_fid} {_year}')
            _c = _f.get('centroids', {}).get(str(_year))
            req(_c is not None, f'missing annual centroid {_fid} {_year}')
            _rows = []
            for _eid in _ids:
                req(_eid in _mst_lookup, f'MST member absent from target-excluded scan: {_eid}')
                _e = _mst_lookup[_eid]
                _vge = max(abs(float(_e['vg'])), 1e-12)
                _vgc = max(abs(float(_c['vg'])), 1e-12)
                _rows.append([
                    _mst_signed_circular_delta_deg(_e['sol'], _c['sol']) / 10.0,
                    _mst_signed_circular_delta_deg(_e['sun_lon'], _c['sun_lon']) / 4.0,
                    (float(_e['ecl_lat']) - float(_c['ecl_lat'])) / 4.0,
                    math.log(_vge/_vgc) / math.log(1.10),
                ])
            _value = _mst_bottleneck_share(_rows)
            _values[_fi] = _value
            _year_occurrences += len(_ids)
            if len(_ids) == 1:
                _singleton_families += 1
            if _value == 0.0:
                _zero_total_families += 1
        req(_values.shape == (4504,) and np.isfinite(_values).all(), f'invalid MST annual vector {_year}')
        req(np.all((_values >= 0.0) & (_values <= 1.0)), f'MST annual vector range invalid {_year}')
        _mst_columns.append(_values)
        _mst_total_occurrences += _year_occurrences
        _mst_year_meta.append({
            'year': _year,
            'member_occurrences': _year_occurrences,
            'singleton_families': _singleton_families,
            'zero_feature_families': _zero_total_families,
            'feature_sha256': array_sha(_values),
        })

    req(_mst_total_occurrences == 74497, f'MST total member-occurrence provenance changed: {_mst_total_occurrences}')
    mst_bottleneck2 = np.column_stack(_mst_columns)
    req(mst_bottleneck2.shape == (4504,2) and np.isfinite(mst_bottleneck2).all(), f'invalid MST topology matrix {mst_bottleneck2.shape}')
    mst_bottleneck2_sha256 = array_sha(mst_bottleneck2)
'''

INSERT_POST_PARENT = r'''

    _mst_parent_expected = {
        'recovered_at_25': 22,
        'recovered_at_50': 43,
        'recovered_at_100': 80,
        'recovered_at_500': 171,
        'qualified_matches': 256,
        'top100_dominant_precision': 0.8075287489258385,
        'mrr': 0.02016666446026534,
    }
    assert_metrics(share_metrics, _mst_parent_expected, '#1194 representative-share parent')
    req(order_sha(share_order) == 'a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592', '#1194 parent order changed')
    req(x.shape == (4504,34) and np.isfinite(x).all(), f'parent feature matrix changed: {x.shape}')
    req(mst_bottleneck2.shape == (4504,2), 'MST feature shape changed')

    _mst_x36 = np.column_stack([x, mst_bottleneck2])
    req(_mst_x36.shape == (4504,36) and np.isfinite(_mst_x36).all(), f'invalid MST successor matrix {_mst_x36.shape}')

    _mst_oof = np.zeros(len(ids), dtype=float)
    _mst_fold_diag = []
    for _fold in range(5):
        _tr = folds != _fold
        _te = folds == _fold
        req(_tr.any() and _te.any(), f'empty MST fold {_fold}')
        req({groups[i] for i in np.where(_tr)[0]}.isdisjoint({groups[i] for i in np.where(_te)[0]}), f'MST group leakage fold {_fold}')
        _model = qmod.model()
        _model.fit(_mst_x36[_tr], y_share[_tr], sample_weight=weights[_tr])
        _mst_oof[_te] = _model.predict(_mst_x36[_te])
        _mst_fold_diag.append({'fold':_fold,'train':int(_tr.sum()),'test':int(_te.sum())})
    req(np.isfinite(_mst_oof).all(), 'MST OOF prediction invalid')

    _mst_idx = qmod.diversity_order(_mst_oof, cm, DIVERSITY['lambda'], DIVERSITY['scale'], tie)
    _mst_order = [ids[i] for i in _mst_idx]
    req(len(_mst_order)==4504 and len(set(_mst_order))==4504 and set(_mst_order)==set(ids), 'MST successor changed family universe')
    _mst_metrics = qmod.v1.monotone_metrics(fams, _mst_order, truths, eligible)

    _mst_gates = {
        'recovered_at_100_gt_80': int(_mst_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_mst_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_mst_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_mst_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_mst_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_mst_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_mst_metrics['qualified_matches']) == 256,
    }
    _mst_passed = all(_mst_gates.values())

    _mst_full = {'frozen':False,'model_sha256':None}
    if _mst_passed:
        _full_model = qmod.model()
        _full_model.fit(_mst_x36, y_share, sample_weight=weights)
        _full_path = a.output / 'orbittrace_gmn_mst_bottleneck_topology_extratrees.joblib'
        joblib.dump(_full_model, _full_path)
        _mst_full = {'frozen':True,'model_class':type(_full_model).__name__,'model_sha256':sha(_full_path)}

    _mst_result = {
        'stage':'GMN_TARGET_EXCLUDED_MST_BOTTLENECK_TOPOLOGY_V1',
        'scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict':'PASS_GMN_MST_BOTTLENECK_TOPOLOGY_V1' if _mst_passed else 'FAIL_GMN_MST_BOTTLENECK_TOPOLOGY_V1',
        'candidate_counts':{'hard':226,'p19':1075,'p20':3203,'union':4504},
        'feature_dimensions':{'parent':34,'mst_bottleneck_added':2,'successor':36},
        'mst_definition':'deterministic_prim_largest_edge_over_total_edge_length_per_year',
        'mst_feature_matrix_sha256':mst_bottleneck2_sha256,
        'annual_feature_provenance':_mst_year_meta,
        'annual_feature_min':[float(np.min(mst_bottleneck2[:,0])),float(np.min(mst_bottleneck2[:,1]))],
        'annual_feature_median':[float(np.median(mst_bottleneck2[:,0])),float(np.median(mst_bottleneck2[:,1]))],
        'annual_feature_max':[float(np.max(mst_bottleneck2[:,0])),float(np.max(mst_bottleneck2[:,1]))],
        'parent_feature_matrix_sha256':array_sha(x),
        'successor_feature_matrix_sha256':array_sha(_mst_x36),
        'parent':trimmed(share_metrics),
        'parent_order_sha256':order_sha(share_order),
        'successor':trimmed(_mst_metrics),
        'successor_order_sha256':order_sha(_mst_order),
        'folds':_mst_fold_diag,
        'gates':_mst_gates,
        'full_model':_mst_full,
        'tree_algorithm':'deterministic_prim_start_vertex_0_smallest_vertex_index_ties',
        'singletons_defined_as_zero':True,
        'all_zero_tree_defined_as_zero':True,
        'threshold_or_radius_used':False,
        'density_or_core_distance_used':False,
        'hdbscan_or_dbscan_run':False,
        'candidate_generation_changed':False,
        'target_changed':False,
        'folds_changed':False,
        'sample_weights_changed':False,
        'estimator_changed':False,
        'diversity_changed':False,
        'family_membership_changed':False,
        'candidate_identity_changed':False,
        'feature_selection':False,
        'topology_parameter_search':False,
        'post_result_second_search':False,
        'blind_exclusion':[20.0,55.0],
        'sonotaco_2013_2014_access':False,
        'sonotaco_feature_access':False,
        'target_information_access':False,
        'target_region_events_accessed':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
    }
    _out = a.output / 'GMN_MST_BOTTLENECK_TOPOLOGY_V1.json'
    _out.write_text(json.dumps(_mst_result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(_mst_result,indent=2,sort_keys=True))
'''


def git_blob_sha(data: bytes) -> str:
    h=hashlib.sha1(); h.update(f"blob {len(data)}\0".encode()); h.update(data); return h.hexdigest()


def main() -> int:
    parent_path=Path(os.environ['ORBITTRACE_REPRESENTATIVE_SHARE_PARENT_SOURCE'])
    if not parent_path.is_file(): raise RuntimeError(f'missing exact #1194 parent source: {parent_path}')
    data=parent_path.read_bytes()
    if git_blob_sha(data)!=PARENT_GIT_BLOB: raise RuntimeError('exact #1194 parent Git blob changed')
    source=data.decode('utf-8')
    if source.count(ANCHOR_PRETRUTH)!=1 or source.count(ANCHOR_POST_PARENT)!=1: raise RuntimeError('frozen injection anchor changed')
    patched=source.replace(ANCHOR_PRETRUTH,ANCHOR_PRETRUTH+INSERT_PRETRUTH,1)
    patched=patched.replace(ANCHOR_POST_PARENT,ANCHOR_POST_PARENT+INSERT_POST_PARENT,1)
    ns={'__name__':'__main__','__file__':str(parent_path),'__package__':None}
    exec(compile(patched,str(parent_path),'exec'),ns,ns)
    return 0

if __name__=='__main__': raise SystemExit(main())
