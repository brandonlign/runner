#!/usr/bin/env python3
"""Frozen Drummond (1981) D_D orbital dissimilarity for P3 external stress testing.

This module is validation-only.  P3 itself continues to use the already-frozen
Southworth-Hawkins D_SH feature.  D_D is evaluated only after P3 external
memberships and deterministic controls have been frozen.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

_EPS = 1e-15


def _unit_plane_normal(i_deg: float, node_deg: float) -> np.ndarray:
    i = math.radians(float(i_deg))
    node = math.radians(float(node_deg))
    # Unit specific-angular-momentum direction for the standard Ω,i convention.
    return np.asarray([
        math.sin(i) * math.sin(node),
        -math.sin(i) * math.cos(node),
        math.cos(i),
    ], dtype=np.float64)


def _unit_perihelion_vector(i_deg: float, arg_deg: float, node_deg: float) -> np.ndarray:
    i = math.radians(float(i_deg))
    arg = math.radians(float(arg_deg))
    node = math.radians(float(node_deg))
    # Unit eccentricity/Laplace-vector direction toward perihelion.
    return np.asarray([
        math.cos(node) * math.cos(arg) - math.sin(node) * math.sin(arg) * math.cos(i),
        math.sin(node) * math.cos(arg) + math.cos(node) * math.sin(arg) * math.cos(i),
        math.sin(arg) * math.sin(i),
    ], dtype=np.float64)


def _angle(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if not math.isfinite(denom) or denom <= _EPS:
        raise ValueError('undefined orbital-vector angle')
    cosine = float(np.dot(a, b) / denom)
    return math.acos(float(np.clip(cosine, -1.0, 1.0)))


def drummond_dd(
    q1: float, e1: float, i1_deg: float, arg1_deg: float, node1_deg: float,
    q2: float, e2: float, i2_deg: float, arg2_deg: float, node2_deg: float,
) -> float:
    """Return the dimensionless Drummond D_D dissimilarity.

    Formula follows Drummond (1981), as reproduced in modern meteor D-criterion
    comparisons: relative q/e differences plus normalized plane-angle I and
    apsidal/eccentricity-vector angle theta terms.
    """
    vals = np.asarray([q1,e1,i1_deg,arg1_deg,node1_deg,q2,e2,i2_deg,arg2_deg,node2_deg], dtype=np.float64)
    if not np.all(np.isfinite(vals)):
        raise ValueError('non-finite orbital element')
    q1=float(q1); q2=float(q2); e1=float(e1); e2=float(e2)
    if q1 <= 0.0 or q2 <= 0.0 or e1 < 0.0 or e2 < 0.0:
        raise ValueError('invalid q/e for D_D')
    qsum=q1+q2; esum=e1+e2
    if qsum <= _EPS or esum <= _EPS:
        raise ValueError('undefined relative q/e denominator for D_D')
    h1=_unit_plane_normal(i1_deg,node1_deg); h2=_unit_plane_normal(i2_deg,node2_deg)
    p1=_unit_perihelion_vector(i1_deg,arg1_deg,node1_deg); p2=_unit_perihelion_vector(i2_deg,arg2_deg,node2_deg)
    I=_angle(h1,h2)
    theta=_angle(p1,p2)
    qterm=(q1-q2)/qsum
    eterm=(e1-e2)/esum
    dd2=qterm*qterm + eterm*eterm + (I/math.pi)**2 + (((e1+e2)/2.0)*(theta/math.pi))**2
    if not math.isfinite(dd2) or dd2 < -1e-14:
        raise ValueError('invalid D_D square')
    return math.sqrt(max(0.0,dd2))


def minimum_drummond_dd(orbit: dict[str,float], seeds: Iterable[dict[str,float]]) -> float:
    values=[]
    for seed in seeds:
        values.append(drummond_dd(
            orbit['q'],orbit['e'],orbit['i'],orbit['arg'],orbit['node'],
            seed['q'],seed['e'],seed['i'],seed['arg'],seed['node'],
        ))
    if not values:
        raise ValueError('empty opposite-year seed set')
    result=float(min(values))
    if not math.isfinite(result):
        raise ValueError('non-finite minimum D_D')
    return result


def self_test() -> dict[str,bool]:
    a=dict(q=0.8,e=0.6,i=20.0,arg=40.0,node=80.0)
    b=dict(q=0.9,e=0.7,i=25.0,arg=55.0,node=95.0)
    c=dict(q=1.0,e=0.3,i=5.0,arg=220.0,node=12.0)
    daa=drummond_dd(a['q'],a['e'],a['i'],a['arg'],a['node'],a['q'],a['e'],a['i'],a['arg'],a['node'])
    dab=drummond_dd(a['q'],a['e'],a['i'],a['arg'],a['node'],b['q'],b['e'],b['i'],b['arg'],b['node'])
    dba=drummond_dd(b['q'],b['e'],b['i'],b['arg'],b['node'],a['q'],a['e'],a['i'],a['arg'],a['node'])
    # Common rotation of both Ω values about the reference z-axis leaves relative geometry unchanged.
    r1=drummond_dd(a['q'],a['e'],a['i'],a['arg'],a['node']+37.0,b['q'],b['e'],b['i'],b['arg'],b['node']+37.0)
    return {
        'identity_zero': abs(daa) <= 1e-12,
        'symmetric': abs(dab-dba) <= 1e-14,
        'nonnegative': dab >= 0.0,
        'common_node_rotation_invariant': abs(dab-r1) <= 1e-14,
        'minimum_exact': abs(minimum_drummond_dd(a,[b,c])-min(
            drummond_dd(a['q'],a['e'],a['i'],a['arg'],a['node'],b['q'],b['e'],b['i'],b['arg'],b['node']),
            drummond_dd(a['q'],a['e'],a['i'],a['arg'],a['node'],c['q'],c['e'],c['i'],c['arg'],c['node']),
        )) <= 1e-14,
    }


if __name__ == '__main__':
    result=self_test()
    print(result)
    raise SystemExit(0 if all(result.values()) else 1)
