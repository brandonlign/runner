"""Cross-fitted v3.3 membership with a deterministic permutation background."""
from __future__ import annotations
import hashlib
from typing import Any
import numpy as np
from pipeline.unified_v2.crossfit_membership import _bh_qvalues,_distances,_membership_pvalues,_robust_center_scale
from .config import V3Config

def _permutation_background_pvalues(held_values:np.ndarray,scores:np.ndarray,center:np.ndarray,scale:np.ndarray,event_ids:np.ndarray,shifts:int)->np.ndarray:
    if held_values.shape[1]!=6: raise ValueError("v3.3 permutation membership requires periodic_physical6")
    order=np.asarray(sorted(range(len(event_ids)),key=lambda index: hashlib.sha256(str(event_ids[index]).encode()).digest()),dtype=int)
    solar_pair=held_values[order,:2].copy(); null_scores=[]
    for step in range(1,int(shifts)+1):
        offset=max(1,int(round(step*len(order)/(int(shifts)+1)))); permuted=held_values.copy(); permuted[order,:2]=np.roll(solar_pair,offset,axis=0); null_scores.append(_distances(permuted,center,scale,None))
    pooled=np.sort(np.concatenate(null_scores)); lower_equal=np.searchsorted(pooled,scores,side="right"); return (1.0+lower_equal.astype(float))/(len(pooled)+1.0)

def expand_candidate(candidate:dict[str,Any],matrix:np.ndarray,years:np.ndarray,event_ids:np.ndarray,config:V3Config)->dict[str,Any]:
    values=np.asarray(matrix,dtype=float); year_array=np.asarray(years,dtype=np.int64); ids=np.asarray(event_ids,dtype=str); members=np.unique(np.asarray(candidate.get("members",()),dtype=int))
    if values.ndim!=2 or values.shape[0]!=len(year_array) or len(ids)!=len(values): raise ValueError("matrix, years, and event_ids must align")
    if len(members)<config.halo_min_training_members: raise ValueError("candidate has too few core members")
    expanded={int(value) for value in members}; iteration_folds=[]
    for _iteration in range(int(config.halo_iterations)):
        snapshot=np.asarray(sorted(expanded),dtype=int); additions:set[int]=set(); folds:dict[str,Any]={}
        for year in sorted(int(value) for value in np.unique(year_array)):
            heldout=np.flatnonzero(year_array==year); training=snapshot[year_array[snapshot]!=year]
            if len(training)<config.halo_min_training_members or not len(heldout):
                folds[str(year)]={"skipped":True,"training_active_members":int(len(training)),"heldout_events":int(len(heldout))}; continue
            center,scale=_robust_center_scale(values[training],config.halo_scale_floor); core_scores=_distances(values[training],center,scale,None)
            cutoff=float(np.quantile(core_scores,1.0-config.halo_core_tail_alpha)*config.halo_cutoff_inflation); scores=_distances(values[heldout],center,scale,None); conformity=_membership_pvalues(core_scores,scores)
            background_p=_permutation_background_pvalues(values[heldout],scores,center,scale,ids[heldout],int(config.halo_background_shifts)); background_q=_bh_qvalues(background_p); accepted_mask=scores<=cutoff
            if config.halo_enforce_density_fdr: accepted_mask &= background_q<=config.halo_density_fdr
            accepted=heldout[accepted_mask]; new={int(value) for value in accepted if int(value) not in snapshot}; additions.update(new)
            folds[str(year)]={"skipped":False,"training_active_members":int(len(training)),"heldout_events":int(len(heldout)),"accepted_events":int(len(accepted)),"new_events":int(len(new)),"core_cutoff":cutoff,"mean_accepted_conformity":float(np.mean(conformity[accepted_mask])) if bool(accepted_mask.any()) else None,"max_accepted_background_q":float(np.max(background_q[accepted_mask])) if bool(accepted_mask.any()) else None}
        expanded.update(additions); iteration_folds.append(folds)
        if not additions: break
    expanded_indices=np.asarray(sorted(expanded),dtype=int); result=dict(candidate); result["core_members"]=[int(value) for value in members.tolist()]; result["expanded_members"]=[int(value) for value in expanded_indices.tolist()]; result["expanded_event_ids"]=[str(value) for value in ids[expanded_indices].tolist()]; result["expanded_member_count"]=int(len(expanded_indices)); result["halo_added_count"]=int(len(expanded_indices)-len(members)); result["crossfit_halo"]={"method":"leave-one-year-out robust envelope plus solar-pair permutation-background FDR","background_shifts":int(config.halo_background_shifts),"density_fdr":float(config.halo_density_fdr),"density_fdr_enforced":bool(config.halo_enforce_density_fdr),"core_tail_alpha":float(config.halo_core_tail_alpha),"cutoff_inflation":float(config.halo_cutoff_inflation),"iterations_run":int(len(iteration_folds)),"iterations":iteration_folds,"folds":iteration_folds[-1] if iteration_folds else {}}
    return result

__all__=["expand_candidate"]
