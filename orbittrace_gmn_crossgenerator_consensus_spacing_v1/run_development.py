#!/usr/bin/env python3
"""Execute the frozen cross-generator consensus spacing successor.

This wrapper imports the exact PR #1194 scientific source by Git-blob identity,
adds only the preregistered direct-edge first-pass/backfill evaluation immediately
after the exact #1194 representative-share OOF order is formed, and then lets the
parent source complete unchanged.
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

PARENT_GIT_BLOB = "340f9d54b42ba2500652d7f0a74f22bbd3354f2e"
PARENT_ORDER_SHA256 = "a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592"
GRAPH_FILE_SHA256 = "1d7ccb41800b222df053e1f8240ceb2c21020ae160e0c6e6b33eda0b546b03ac"
GRAPH_CANONICAL_EDGE_SHA256 = "319d1a868d68148221caba82e28ca17b9a7f55b0f1f7b0f1c02a8fc9e5c28bb0"
GRAPH_EDGE_COUNT = 698
EXPECTED_UNION = 4504

ANCHOR = "    share_metrics = qmod.v1.monotone_metrics(fams, share_order, truths, eligible)\n"

INSERT = r'''

    # Frozen successor: direct-edge first-pass spacing over the immutable
    # cross-generator graph, with every deferred family appended in exact
    # #1194 parent relative order. No graph/component/model/membership change.
    _os = __import__('os')
    _graph_path = Path(_os.environ['ORBITTRACE_FROZEN_GRAPH_JSON'])
    _graph_bytes = _graph_path.read_bytes()
    req(hashlib.sha256(_graph_bytes).hexdigest() == '1d7ccb41800b222df053e1f8240ceb2c21020ae160e0c6e6b33eda0b546b03ac', 'frozen graph file changed')
    _graph = json.loads(_graph_bytes)
    req(_graph.get('pretruth_graph_frozen') is True, 'graph was not frozen pretruth')
    req(_graph.get('labels_loaded') is False and _graph.get('truth_accessed') is False, 'graph contains truth access')
    req(_graph.get('candidate_order_evaluated') is False, 'diagnostic graph evaluated candidate order')
    req(_graph.get('membership_changed') is False, 'diagnostic graph changed membership')
    req(_graph.get('edge_count') == 698 and len(_graph.get('edges', [])) == 698, 'graph edge count changed')
    req(_graph.get('canonical_edge_sha256') == '319d1a868d68148221caba82e28ca17b9a7f55b0f1f7b0f1c02a8fc9e5c28bb0', 'canonical graph edge identity changed')
    req(_graph.get('candidate_counts') == {'hard': 226, 'p19': 1075, 'p20': 3203, 'union': 4504}, 'graph universe changed')
    req(_graph.get('blind_exclusion') == [20.0, 55.0], 'graph firewall changed')
    req(_graph.get('sonotaco_2013_2014_access') is False and _graph.get('sonotaco_feature_access') is False, 'graph accessed SonotaCo')
    req(_graph.get('target_information_access') is False and _graph.get('target_region_events_accessed') is False, 'graph accessed protected target')
    req(_graph.get('maarsy_scientific_access') is False and _graph.get('dms_scientific_access') is False, 'graph accessed protected external data')

    _expected_parent = {
        'recovered_at_25': 22,
        'recovered_at_50': 43,
        'recovered_at_100': 80,
        'recovered_at_500': 171,
        'qualified_matches': 256,
        'top100_dominant_precision': 0.8075287489258385,
        'mrr': 0.02016666446026534,
    }
    assert_metrics(share_metrics, _expected_parent, '#1194 representative-share parent')
    req(order_sha(share_order) == 'a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592', '#1194 parent order changed')
    req(len(share_order) == 4504 and len(set(share_order)) == 4504, '#1194 parent order universe changed')

    _adj = {fid: set() for fid in share_order}
    _canonical_edges = []
    for _edge in _graph['edges']:
        _p19 = str(_edge['p19_family_id'])
        _p20 = str(_edge['p20_family_id'])
        req(_p19 in _adj and _p20 in _adj, 'graph endpoint absent from parent universe')
        req(source[_p19] == 'p19' and source[_p20] == 'p20', 'graph endpoint source changed')
        req(_p20 not in _adj[_p19] and _p19 not in _adj[_p20], 'duplicate graph edge')
        _adj[_p19].add(_p20)
        _adj[_p20].add(_p19)
        _canonical_edges.append((_p19, _p20))
    req(len(_canonical_edges) == 698, 'graph edge parsing changed')

    _accepted = []
    _deferred = []
    _accepted_set = set()
    for _fid in share_order:
        if _adj[_fid].isdisjoint(_accepted_set):
            _accepted.append(_fid)
            _accepted_set.add(_fid)
        else:
            _deferred.append(_fid)
    _spaced_order = _accepted + _deferred
    req(len(_spaced_order) == 4504 and len(set(_spaced_order)) == 4504, 'spacing changed candidate cardinality')
    req(set(_spaced_order) == set(share_order), 'spacing changed candidate identity set')
    req([fid for fid in _spaced_order if fid in set(_deferred)] == _deferred, 'deferred relative order changed')
    for _u, _v in _canonical_edges:
        req(not (_u in _accepted_set and _v in _accepted_set), 'accepted pass contains a frozen direct conflict')

    _spaced_metrics = qmod.v1.monotone_metrics(fams, _spaced_order, truths, eligible)
    _spacing_gates = {
        'recovered_at_100_gt_80': int(_spaced_metrics['recovered_at_100']) > 80,
        'recovered_at_50_ge_43': int(_spaced_metrics['recovered_at_50']) >= 43,
        'recovered_at_25_ge_22': int(_spaced_metrics['recovered_at_25']) >= 22,
        'recovered_at_500_ge_171': int(_spaced_metrics['recovered_at_500']) >= 171,
        'top100_precision_ge_parent': float(_spaced_metrics['top100_dominant_precision']) >= 0.8075287489258385,
        'mrr_ge_parent': float(_spaced_metrics['mrr']) >= 0.02016666446026534,
        'qualified_matches_eq_256': int(_spaced_metrics['qualified_matches']) == 256,
    }
    _spacing_pass = all(_spacing_gates.values())
    _spacing_result = {
        'stage': 'GMN_TARGET_EXCLUDED_CROSSGENERATOR_CONSENSUS_SPACING_V1',
        'scientific_role': 'TARGET_EXCLUDED_GMN_2022_2023_METHOD_DEVELOPMENT_ONLY',
        'verdict': 'PASS_GMN_CROSSGENERATOR_CONSENSUS_SPACING_V1' if _spacing_pass else 'FAIL_GMN_CROSSGENERATOR_CONSENSUS_SPACING_V1',
        'candidate_counts': {'hard': 226, 'p19': 1075, 'p20': 3203, 'union': 4504},
        'graph_file_sha256': hashlib.sha256(_graph_bytes).hexdigest(),
        'graph_canonical_edge_sha256': _graph['canonical_edge_sha256'],
        'graph_edge_count': len(_canonical_edges),
        'graph_relation_modified': False,
        'connected_component_closure_used': False,
        'graph_score_used': False,
        'source_quota_selected': False,
        'threshold_search': False,
        'top_k_rule_used': False,
        'parent': trimmed(share_metrics),
        'parent_order_sha256': order_sha(share_order),
        'successor': trimmed(_spaced_metrics),
        'successor_order_sha256': order_sha(_spaced_order),
        'first_pass_accepted_count': len(_accepted),
        'deferred_count': len(_deferred),
        'family_deletion': False,
        'membership_changed': False,
        'complete_backfill': True,
        'candidate_order_is_full_permutation': True,
        'gates': _spacing_gates,
        'post_result_second_search': False,
        'blind_exclusion': [20.0, 55.0],
        'sonotaco_2013_2014_access': False,
        'sonotaco_feature_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
    }
    _spacing_output = a.output / 'GMN_CROSSGENERATOR_CONSENSUS_SPACING_V1.json'
    _spacing_output.write_text(json.dumps(_spacing_result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(_spacing_result, indent=2, sort_keys=True))
'''


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def main() -> int:
    parent_path = Path(os.environ["ORBITTRACE_REPRESENTATIVE_SHARE_PARENT_SOURCE"])
    graph_path = Path(os.environ["ORBITTRACE_FROZEN_GRAPH_JSON"])
    if not parent_path.is_file():
        raise RuntimeError(f"missing exact #1194 parent source: {parent_path}")
    if not graph_path.is_file():
        raise RuntimeError(f"missing frozen consensus graph: {graph_path}")

    parent_bytes = parent_path.read_bytes()
    if git_blob_sha(parent_bytes) != PARENT_GIT_BLOB:
        raise RuntimeError("exact #1194 parent Git blob changed")
    graph_bytes = graph_path.read_bytes()
    if hashlib.sha256(graph_bytes).hexdigest() != GRAPH_FILE_SHA256:
        raise RuntimeError("frozen graph file SHA-256 changed")

    source = parent_bytes.decode("utf-8")
    if source.count(ANCHOR) != 1:
        raise RuntimeError("exact #1194 successor injection anchor not unique")
    patched = source.replace(ANCHOR, ANCHOR + INSERT, 1)

    # sys.argv is intentionally passed through unchanged: workflow callers use
    # the exact #1194 CLI. The graph and parent source are environment-bound
    # provenance inputs, not new model parameters.
    namespace = {
        "__name__": "__main__",
        "__file__": str(parent_path),
        "__package__": None,
    }
    exec(compile(patched, str(parent_path), "exec"), namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
