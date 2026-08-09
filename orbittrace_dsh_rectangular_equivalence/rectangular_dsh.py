from __future__ import annotations

from typing import Sequence

import numpy as np


def wrap_pi(value: np.ndarray | float) -> np.ndarray:
    return (np.asarray(value, dtype=np.float64) + np.pi) % (2.0 * np.pi) - np.pi


def _oriented_rectangular_dsh(
    q1_au: Sequence[float] | np.ndarray,
    e1: Sequence[float] | np.ndarray,
    i1_deg: Sequence[float] | np.ndarray,
    peri1_deg: Sequence[float] | np.ndarray,
    node1_deg: Sequence[float] | np.ndarray,
    q2_au: Sequence[float] | np.ndarray,
    e2: Sequence[float] | np.ndarray,
    i2_deg: Sequence[float] | np.ndarray,
    peri2_deg: Sequence[float] | np.ndarray,
    node2_deg: Sequence[float] | np.ndarray,
) -> np.ndarray:
    q1=np.asarray(q1_au,dtype=np.float64); ee1=np.asarray(e1,dtype=np.float64)
    inc1=np.radians(np.asarray(i1_deg,dtype=np.float64)); peri1=np.radians(np.asarray(peri1_deg,dtype=np.float64)); node1=np.radians(np.asarray(node1_deg,dtype=np.float64))
    q2=np.asarray(q2_au,dtype=np.float64); ee2=np.asarray(e2,dtype=np.float64)
    inc2=np.radians(np.asarray(i2_deg,dtype=np.float64)); peri2=np.radians(np.asarray(peri2_deg,dtype=np.float64)); node2=np.radians(np.asarray(node2_deg,dtype=np.float64))
    for group in ((q1,ee1,inc1,peri1,node1),(q2,ee2,inc2,peri2,node2)):
        if not all(x.ndim==1 for x in group) or len({x.shape for x in group})!=1:
            raise ValueError('rectangular D_SH side arrays must be one-dimensional and shape-matched')
        if not np.all(np.isfinite(np.column_stack(group))):
            raise ValueError('non-finite orbital element in rectangular D_SH input')
    if len(q1)==0 or len(q2)==0:
        raise ValueError('rectangular D_SH requires nonempty sides')

    ii1=inc1[:,None]; ii2=inc2[None,:]
    node_delta=wrap_pi(node2[None,:]-node1[:,None])
    cos_i=np.cos(ii1)*np.cos(ii2)+np.sin(ii1)*np.sin(ii2)*np.cos(node_delta)
    mutual_i=np.arccos(np.clip(cos_i,-1.0,1.0))
    denominator=np.cos(0.5*mutual_i)
    numerator=np.cos(0.5*(ii1+ii2))*np.sin(0.5*node_delta)
    ratio=np.divide(numerator,denominator,out=np.zeros_like(numerator),where=np.abs(denominator)>1e-15)
    peri_delta=wrap_pi(peri2[None,:]-peri1[:,None]+2.0*np.arcsin(np.clip(ratio,-1.0,1.0)))
    q_delta=q1[:,None]-q2[None,:]
    e_delta=ee1[:,None]-ee2[None,:]
    plane=2.0*np.sin(0.5*mutual_i)
    peri_term=0.5*(ee1[:,None]+ee2[None,:])*2.0*np.sin(0.5*peri_delta)
    squared=q_delta*q_delta+e_delta*e_delta+plane*plane+peri_term*peri_term
    distance=np.sqrt(np.maximum(squared,0.0))
    if not np.all(np.isfinite(distance)):
        raise ValueError('non-finite rectangular D_SH matrix')
    return distance


def rectangular_pairwise_dsh(
    left: dict[str,np.ndarray], right: dict[str,np.ndarray]
) -> np.ndarray:
    """Return the exact symmetrized cross-slice produced by frozen pairwise_dsh.

    The frozen square implementation averages its raw matrix with its transpose.
    To preserve that floating-point behavior without constructing discarded
    within-left/within-right blocks, compute both rectangular orientations and
    average the forward block with the transposed reverse block.
    """
    keys=('q','e','i','peri','node')
    f=_oriented_rectangular_dsh(*(left[k] for k in keys),*(right[k] for k in keys))
    r=_oriented_rectangular_dsh(*(right[k] for k in keys),*(left[k] for k in keys)).T
    out=0.5*(f+r)
    if not np.all(np.isfinite(out)):
        raise ValueError('non-finite symmetrized rectangular D_SH matrix')
    return out
