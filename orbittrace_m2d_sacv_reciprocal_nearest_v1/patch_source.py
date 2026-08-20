from pathlib import Path
import hashlib

ROOT=Path('orbittrace_m2d_sacv_edge_consensus_v1')

def replace_once(text, old, new, label):
    n=text.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {n}')
    return text.replace(old,new,1)

p=ROOT/'build_pretruth.py'
s=p.read_text()
needle="""                    edges.append({'a':qa['id'],'b':qb['id'],'d':d,'ab':qa['cross_support'],'ba':qb['cross_support']})
        comps=[];seen=set()
"""
replacement="""                    edges.append({'a':qa['id'],'b':qb['id'],'d':d,'ab':qa['cross_support'],'ba':qb['cross_support']})
        # Reciprocal-nearest association is inherited from the pre-reveal promoted M2D v8 lineage (#316).
        # SACV admissibility and reciprocal validation are unchanged; this only prevents a validated
        # hypothesis from linking through a non-nearest cross-year counterpart. Event IDs break exact
        # distance ties deterministically and do not enter any scientific score.
        best_a={};best_b={}
        for e in edges:
            ka=(float(e['d']),str(e['b']));kb=(float(e['d']),str(e['a']))
            if e['a'] not in best_a or ka<best_a[e['a']]:best_a[e['a']]=ka
            if e['b'] not in best_b or kb<best_b[e['b']]:best_b[e['b']]=kb
        edges=[e for e in edges if best_a[e['a']][1]==e['b'] and best_b[e['b']][1]==e['a']]
        adj={}
        for e in edges:
            A='22:'+e['a'];B='23:'+e['b'];adj.setdefault(A,set()).add(B);adj.setdefault(B,set()).add(A)
        comps=[];seen=set()
"""
s=replace_once(s,needle,replacement,'reciprocal-nearest insertion')
s=s.replace('EDGE_CONSENSUS','RECIPROCAL_NEAREST').replace('edge-consensus','reciprocal-nearest').replace('edge_consensus','reciprocal_nearest')
s=replace_once(s,
    "enumerate_all_admissible_annual_hypotheses_then_recurrence_graph_then_max_edge_component_then_reciprocal_nearest_membership",
    "enumerate_all_admissible_annual_hypotheses_then_validated_recurrence_graph_then_reciprocal_nearest_edge_sparsification_then_max_edge_component_then_edge_consensus_membership",
    'architecture metadata')
s=replace_once(s,
    "union_of_endpoint_membership_intersections_over_validated_edges_in_selected_component",
    "union_of_endpoint_membership_intersections_over_reciprocal_nearest_validated_edges_in_selected_component",
    'membership metadata')
p.write_text(s)

for name in ('evaluate_truth.py','run_binding.sh'):
    q=ROOT/name
    t=q.read_text().replace('EDGE_CONSENSUS','RECIPROCAL_NEAREST').replace('edge-consensus','reciprocal-nearest').replace('edge_consensus','reciprocal_nearest')
    q.write_text(t)

q=ROOT/'PROTOCOL.md'
t=q.read_text().replace('EDGE_CONSENSUS','RECIPROCAL_NEAREST').replace('edge-consensus','reciprocal-nearest').replace('edge_consensus','reciprocal_nearest')
t += '''\n\n## Reciprocal-nearest v1 frozen successor delta\n\nThis successor is post-target-reveal development but target-excluded. Its sole scientific change relative to the frozen edge-consensus predecessor is applied **after** every unchanged SACV-admissible annual hypothesis and every unchanged reciprocal validation edge have been constructed: retain only validated edges that are reciprocal nearest by the already-defined physical recurrence distance, with event ID used only for exact-distance tie breaking. This association principle has pre-reveal ancestry in the promoted M2D v8 reciprocal-nearest recurrence rule (#316). The inherited component selector, endpoint-intersection membership semantics, physical metric, seasonal-analog null, contamination convention, support floor, recurrence validation, parent discovery/rank, benchmark gates, and fallback remain unchanged. No radius, threshold, score blend, component selector, frequency requirement, or target-aware tuning is introduced. A valid GMN failure closes this exact formulation; SonotaCo and OrbitTrace are prohibited unless GMN passes.\n'''
q.write_text(t)

for name in ('PROTOCOL.md','build_pretruth.py','evaluate_truth.py','run_binding.sh'):
    q=ROOT/name
    print(name, hashlib.sha256(q.read_bytes()).hexdigest(), len(q.read_bytes()))
