"""Target-free year-label calibration and multiplicity correction."""
from __future__ import annotations
import hashlib
from typing import Any, Sequence
import numpy as np
from scipy.stats import hypergeom

def recurrence_statistic(counts: Sequence[int], exposure: Sequence[int]) -> float:
    observed=np.asarray(counts,dtype=float); available=np.asarray(exposure,dtype=float)
    if observed.ndim!=1 or observed.shape!=available.shape or observed.size<2: raise ValueError("counts and exposure must be aligned vectors with at least two years")
    if np.any(observed<0) or np.any(available<=0) or np.any(observed>available): raise ValueError("invalid counts or exposure")
    size=float(observed.sum())
    if size<=0: return 0.0
    expected_fraction=size/float(available.sum())
    return float(np.min((observed/available)/expected_fraction))

def _exact_two_year_pvalue(counts: np.ndarray, exposure: np.ndarray) -> tuple[float,float,float]:
    total=int(exposure.sum()); size=int(counts.sum())
    support=np.arange(max(0,size-int(exposure[1])),min(size,int(exposure[0]))+1)
    draws=np.column_stack((support,size-support)); scores=np.asarray([recurrence_statistic(row,exposure) for row in draws],dtype=float)
    probabilities=hypergeom.pmf(support,total,int(exposure[0]),size); observed=recurrence_statistic(counts,exposure); tolerance=np.finfo(float).eps*32.0
    p_value=min(1.0,max(0.0,float(probabilities[scores>=observed-tolerance].sum())))
    mean=float(np.sum(scores*probabilities)); variance=float(np.sum((scores-mean)**2*probabilities))
    return p_value,mean,variance**0.5

def calibrate_candidate(candidate: dict[str,Any], exposure: Sequence[int], *, permutations:int, seed:int) -> dict[str,Any]:
    result=dict(candidate); counts=np.asarray(candidate["annual_counts"],dtype=np.int64); available=np.asarray(exposure,dtype=np.int64)
    if int(counts.sum())!=int(candidate["member_count"]): raise ValueError("candidate annual counts do not equal member_count")
    observed=recurrence_statistic(counts,available)
    if len(counts)==2:
        p_value,null_mean,null_sd=_exact_two_year_pvalue(counts,available); engine="exact_hypergeometric"
    else:
        digest=hashlib.sha256(f"{seed}|{candidate['family_id']}".encode()).digest(); local_seed=int.from_bytes(digest[:8],"big",signed=False); rng=np.random.default_rng(local_seed)
        draws=rng.multivariate_hypergeometric(available,int(counts.sum()),size=int(permutations),method="marginals")
        expected_fraction=float(counts.sum())/float(available.sum()); scores=np.min((draws/available[None,:])/expected_fraction,axis=1)
        p_value=float((1+np.sum(scores>=observed))/(len(scores)+1)); null_mean=float(np.mean(scores)); null_sd=float(np.std(scores,ddof=1)) if len(scores)>1 else 0.0; engine="fixed_membership_year_label_permutation"
    result["calibration"]={"engine":engine,"year_blind_candidate_generation":True,"exposure_by_year":[int(value) for value in available.tolist()],"observed_recurrence_ratio":float(observed),"null_mean":null_mean,"null_sd":null_sd,"permutations":0 if len(counts)==2 else int(permutations),"p_value":p_value}
    result["calibrated_p_value"]=p_value; result["recurrence_ratio"]=float(observed); result["recurrence_z"]=float((observed-null_mean)/null_sd) if null_sd>0 else 0.0
    return result

def benjamini_yekutieli_qvalues(p_values: Sequence[float]) -> np.ndarray:
    values=np.asarray(p_values,dtype=float)
    if values.ndim!=1 or np.any(~np.isfinite(values)) or np.any((values<0)|(values>1)): raise ValueError("p_values must be a finite vector in [0, 1]")
    if not len(values): return values.copy()
    order=np.argsort(values,kind="mergesort"); ranked=values[order]; harmonic=float(np.sum(1.0/np.arange(1,len(values)+1)))
    adjusted=ranked*len(values)*harmonic/np.arange(1,len(values)+1); adjusted=np.minimum.accumulate(adjusted[::-1])[::-1]; output=np.empty_like(adjusted); output[order]=np.minimum(adjusted,1.0); return output

__all__=["benjamini_yekutieli_qvalues","calibrate_candidate","recurrence_statistic"]
