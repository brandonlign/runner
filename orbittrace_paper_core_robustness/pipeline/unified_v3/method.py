"""Frozen ACRF-v3.5 candidate generator used for paper robustness."""
from __future__ import annotations
import hashlib
from typing import Any,Sequence
import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability
from pipeline.unified_v2.features import circular_difference_deg
from pipeline.unified_v2.recurrent_tree import _install_hdbscan_compatibility,_leaf_labels,fit_recurrent_hierarchy
from .calibration import benjamini_yekutieli_qvalues,calibrate_candidate
from .config import V3Config


def _perihelion_vector(orbits:np.ndarray)->np.ndarray:
    inc=np.deg2rad(orbits[:,2]); arg=np.deg2rad(orbits[:,3]); node=np.deg2rad(orbits[:,4])
    return np.column_stack((np.cos(node)*np.cos(arg)-np.sin(node)*np.sin(arg)*np.cos(inc),np.sin(node)*np.cos(arg)+np.cos(node)*np.sin(arg)*np.cos(inc),np.sin(arg)*np.sin(inc)))

def _orbit_distance(a:np.ndarray,b:np.ndarray)->np.ndarray:
    e1,q1=a[:,0][:,None],a[:,1][:,None]; e2,q2=b[:,0][None,:],b[:,1][None,:]
    i1,n1=np.deg2rad(a[:,2])[:,None],np.deg2rad(a[:,4])[:,None]; i2,n2=np.deg2rad(b[:,2])[None,:],np.deg2rad(b[:,4])[None,:]
    plane=np.arccos(np.clip(np.cos(i1)*np.cos(i2)+np.sin(i1)*np.sin(i2)*np.cos(n1-n2),-1.0,1.0)); peri=np.arccos(np.clip(_perihelion_vector(a)@_perihelion_vector(b).T,-1.0,1.0))
    distance2=(e1-e2)**2+(q1-q2)**2+(2.0*np.sin(plane/2.0))**2+(((e1+e2)/2.0)*2.0*np.sin(peri/2.0))**2
    return np.sqrt(np.maximum(distance2,0.0))

def _apply_orbit_gate(candidate:dict[str,Any],orbit_matrix:np.ndarray|None,event_ids:np.ndarray,config:V3Config)->dict[str,Any]:
    result=dict(candidate); expanded=np.asarray(candidate.get("expanded_members",()),dtype=int)
    if orbit_matrix is None:
        final=expanded; result["orbit_coherence"]={"applied":False,"reason":"orbit_fields_unavailable"}
    else:
        values=np.asarray(orbit_matrix,dtype=float); core=np.asarray(candidate.get("core_members",candidate.get("members",())),dtype=int); valid_core=np.isfinite(values[core]).all(axis=1)
        if int(valid_core.sum())<config.halo_min_training_members:
            final=expanded; result["orbit_coherence"]={"applied":False,"reason":"insufficient_valid_core_orbits","valid_core":int(valid_core.sum())}
        else:
            core_orbits=values[core][valid_core]; pairwise=_orbit_distance(core_orbits,core_orbits); medoid=core_orbits[int(np.argmin(np.median(pairwise,axis=1)))]; valid=np.isfinite(values[expanded]).all(axis=1); distances=np.full(len(expanded),np.inf,dtype=float)
            if bool(valid.any()): distances[valid]=_orbit_distance(values[expanded][valid],medoid[None,:])[:,0]
            final=expanded[valid&(distances<=float(config.halo_orbit_distance_max))]; result["orbit_coherence"]={"applied":True,"valid_core":int(valid_core.sum()),"valid_expanded":int(valid.sum()),"distance_max":float(config.halo_orbit_distance_max),"medoid":medoid.tolist(),"kept":int(len(final)),"removed":int(len(expanded)-len(final))}
    result["final_members"]=[int(value) for value in final.tolist()]; result["final_event_ids"]=[str(value) for value in event_ids[final].tolist()]; result["final_member_count"]=int(len(final)); return result

def _family_id(prefix:str,event_ids:Sequence[str])->str:
    payload="|".join(sorted(map(str,event_ids))).encode(); return prefix+hashlib.sha256(payload).hexdigest()[:20]

def _stable_cap(indices:np.ndarray,event_ids:np.ndarray,limit:int,salt:str)->np.ndarray:
    if len(indices)<=limit:return np.sort(indices)
    scored=sorted((hashlib.sha256(f"{salt}|{event_ids[index]}".encode()).digest(),int(index)) for index in indices)
    return np.sort(np.asarray([index for _digest,index in scored[:limit]],dtype=np.int64))

def _candidate(prefix:str,method:str,members:np.ndarray,event_ids:np.ndarray,years:np.ndarray,year_values:tuple[int,...],*,membership_probability:float)->dict[str,Any]:
    ids=tuple(sorted(str(event_ids[index]) for index in members)); counts=tuple(int(np.sum(years[members]==year)) for year in year_values)
    return {"family_id":_family_id(prefix,ids),"hierarchy_method":method,"event_ids":list(ids),"members":[int(value) for value in members.tolist()],"member_count":int(len(members)),"year_values":[int(value) for value in year_values],"annual_counts":[int(value) for value in counts],"members_by_year":{str(year):int(count) for year,count in zip(year_values,counts)},"mean_membership_probability":float(membership_probability)}

def _fit_year_blind_hierarchy(matrix:np.ndarray,years:np.ndarray,event_ids:np.ndarray,config:V3Config)->tuple[list[dict[str,Any]],dict[str,Any]]:
    _install_hdbscan_compatibility(); values=np.asarray(matrix,dtype=float); year_array=np.asarray(years,dtype=np.int64); ids=np.asarray(event_ids,dtype=str); minimum=max(int(config.min_cluster_size)*2,int(config.min_samples)+1)
    if values.ndim!=2 or values.shape[0]!=len(year_array) or len(ids)!=len(year_array):raise ValueError("matrix, years, and event_ids must align")
    if len(values)<minimum:return [],{"events":int(len(values)),"skipped":True,"reason":"too_few_rows"}
    model=hdbscan.HDBSCAN(min_cluster_size=int(config.min_cluster_size),min_samples=int(config.min_samples),metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=int(config.core_dist_n_jobs)).fit(values)
    year_values=tuple(sorted(int(value) for value in np.unique(year_array))); candidates:list[dict[str,Any]]=[]
    for label in sorted(int(value) for value in np.unique(model.labels_) if int(value)>=0):
        members=np.flatnonzero(model.labels_==label)
        if len(members)<config.min_cluster_size:continue
        candidates.append(_candidate("MS3E","year_blind_eom",members,ids,year_array,year_values,membership_probability=float(np.mean(model.probabilities_[members]))))
    tree=model.condensed_tree_._raw_tree; leaf_labels,leaf_probabilities=_leaf_labels(tree,compute_stability(tree))
    for label in sorted(int(value) for value in np.unique(leaf_labels) if int(value)>=0):
        members=np.flatnonzero(leaf_labels==label)
        if len(members)<config.min_cluster_size:continue
        candidates.append(_candidate("MS3L","year_blind_leaf",members,ids,year_array,year_values,membership_probability=float(np.mean(leaf_probabilities[members]))))
    return candidates,{"events":int(len(values)),"dimensions":int(values.shape[1]),"year_labels_used_during_tree_or_membership_generation":False,"eom_candidates":int(sum(item["hierarchy_method"]=="year_blind_eom" for item in candidates)),"leaf_candidates":int(sum(item["hierarchy_method"]=="year_blind_leaf" for item in candidates)),"skipped":False}

def _candidate_order(candidate:dict[str,Any])->tuple[Any,...]:
    return (-len(candidate.get("supporting_windows",())),-float(candidate.get("seed_score") or 0.0),float(candidate["calibrated_p_value"]),-float(candidate["recurrence_z"]),-float(candidate["recurrence_ratio"]),-float(candidate.get("mean_membership_probability") or 0.0),-int(candidate["member_count"]),str(candidate["family_id"]))

def _deduplicate(candidates:Sequence[dict[str,Any]],threshold:float)->tuple[list[dict[str,Any]],int]:
    ordered=sorted((dict(item) for item in candidates),key=_candidate_order); kept:list[dict[str,Any]]=[]; kept_sets:list[set[str]]=[]; event_to_kept:dict[str,set[int]]={}; removed=0
    for candidate in ordered:
        members=set(map(str,candidate["event_ids"])); possible:set[int]=set()
        for event_id in members:possible.update(event_to_kept.get(event_id,()))
        duplicate:int|None=None
        for index in sorted(possible):
            other=kept_sets[index]
            if len(members&other)/len(members|other)>=float(threshold):duplicate=index;break
        if duplicate is not None:
            kept_method=str(kept[duplicate].get("hierarchy_method")); candidate_method=str(candidate.get("hierarchy_method"))
            if kept_method!=candidate_method:
                fused_members=sorted(set(map(int,kept[duplicate].get("members",())))|set(map(int,candidate.get("members",())))); fused_ids=sorted(set(map(str,kept[duplicate]["event_ids"]))|set(map(str,candidate["event_ids"])))
                kept[duplicate]["members"]=fused_members; kept[duplicate]["event_ids"]=fused_ids; kept[duplicate]["member_count"]=int(len(fused_ids)); methods=set(kept[duplicate].get("fused_hierarchy_methods",(kept_method,)));methods.add(candidate_method);kept[duplicate]["fused_hierarchy_methods"]=sorted(methods);kept_sets[duplicate]=set(fused_ids)
                for event_id in fused_ids:event_to_kept.setdefault(event_id,set()).add(duplicate)
            support=set(kept[duplicate].get("supporting_scales",()));support.update(candidate.get("supporting_scales",()));kept[duplicate]["supporting_scales"]=sorted(map(str,support));windows=set(kept[duplicate].get("supporting_windows",()));windows.update(candidate.get("supporting_windows",()));kept[duplicate]["supporting_windows"]=sorted(float(value) for value in windows);removed+=1;continue
        index=len(kept);kept.append(candidate);kept_sets.append(members)
        for event_id in members:event_to_kept.setdefault(event_id,set()).add(index)
    return kept,removed

def _remove_anchor_duplicates(candidates:Sequence[dict[str,Any]],anchors:Sequence[dict[str,Any]],threshold:float)->tuple[list[dict[str,Any]],int]:
    anchor_sets=[set(map(str,anchor["event_ids"])) for anchor in anchors]; output=[]; removed=0
    for candidate in candidates:
        members=set(map(str,candidate["event_ids"]))
        if any(len(members&anchor)/len(members|anchor)>=threshold for anchor in anchor_sets):removed+=1
        else:output.append(candidate)
    return output,removed

def generate_multiscale_candidates(matrix:np.ndarray,years:np.ndarray,event_ids:np.ndarray,solar_longitude_deg:np.ndarray,config:V3Config|None=None)->tuple[list[dict[str,Any]],dict[str,Any]]:
    config=config or V3Config();values=np.asarray(matrix,dtype=float);year_array=np.asarray(years,dtype=np.int64);ids=np.asarray(event_ids,dtype=str);solar=np.asarray(solar_longitude_deg,dtype=float)
    if values.ndim!=2 or values.shape[0]!=len(year_array) or len(ids)!=len(year_array):raise ValueError("matrix, years, and event_ids must align")
    if solar.shape!=(len(values),) or not np.isfinite(solar).all():raise ValueError("solar_longitude_deg must be finite and align with rows")
    if len(set(ids.tolist()))!=len(ids):raise ValueError("event_ids must be unique")
    year_values=tuple(sorted(int(value) for value in np.unique(year_array)))
    if len(year_values)<2:raise ValueError("at least two observing years are required")
    raw=[];scale_diagnostics=[]
    global_parts=[_stable_cap(np.flatnonzero(year_array==year),ids,int(config.hierarchy_max_rows_per_year),f"{config.hierarchy_sample_seed}|global|{year}") for year in year_values];global_selected=np.sort(np.concatenate(global_parts))
    anchor_parents,_anchor_leaves,anchor_diagnostics=fit_recurrent_hierarchy(values[global_selected],year_array[global_selected],ids[global_selected],config,include_leaves=False);full_index={event_id:index for index,event_id in enumerate(ids.tolist())};anchors=[]
    for candidate in anchor_parents:
        supported=np.asarray(candidate["annual_counts"],dtype=int)>=int(config.min_year_events)
        if float(np.mean(supported))<float(config.min_year_support_fraction):continue
        anchor=dict(candidate);anchor["members"]=[full_index[str(value)] for value in anchor["event_ids"]];anchor["scale"]="global_recurrent_anchor";anchor["supporting_scales"]=["global_recurrent_anchor"];anchor["supporting_windows"]=[];anchor["membership_mode"]="hierarchy_core";anchor["anchor_recurrent_rank"]=int(candidate["rank"]);anchors.append(anchor)
        if len(anchors)>=int(config.global_anchor_count):break
    global_candidates,global_diagnostics=_fit_year_blind_hierarchy(values[global_selected],year_array[global_selected],ids[global_selected],config);global_exposure=[int(np.sum(year_array[global_selected]==year)) for year in year_values]
    for candidate in global_candidates:candidate["scale"]="global";candidate["supporting_scales"]=["global"];candidate["supporting_windows"]=[];candidate["calibration_exposure_by_year"]=list(global_exposure)
    raw.extend(global_candidates);scale_diagnostics.append({"scale":"global","exposure":global_exposure,**global_diagnostics})
    half_width=float(config.hierarchy_window_width_deg)/2.0;centers=np.arange(0.0,360.0,float(config.hierarchy_window_stride_deg))
    for center in centers:
        within=np.abs(circular_difference_deg(solar,center))<=half_width;selected_parts=[];exposure=[]
        for year in year_values:
            indices=np.flatnonzero(within&(year_array==year))
            if len(indices)<config.min_cluster_size:selected_parts=[];break
            chosen=_stable_cap(indices,ids,int(config.hierarchy_max_rows_per_year),f"{config.hierarchy_sample_seed}|local|{center:.6f}|{year}");selected_parts.append(chosen);exposure.append(int(len(chosen)))
        if not selected_parts:continue
        selected=np.sort(np.concatenate(selected_parts));local_parents,local_leaves,diagnostics=fit_recurrent_hierarchy(values[selected],year_array[selected],ids[selected],config,include_leaves=True);local=[*local_parents,*local_leaves]
        for candidate in local:
            candidate["scale"]="local_10deg";candidate["window_center_deg"]=float(center);candidate["window_width_deg"]=float(config.hierarchy_window_width_deg);candidate["supporting_scales"]=["local_10deg"];candidate["supporting_windows"]=[float(center)];candidate["calibration_exposure_by_year"]=list(exposure);recurrent=candidate.get("recurrent_stability")
            if recurrent is not None:candidate["seed_score"]=float(recurrent)
            else:
                annual=np.asarray(candidate.get("annual_normalized_stability",()),dtype=float);candidate["seed_score"]=float(np.quantile(annual,config.recurrence_quantile,method="lower")) if len(annual) else 0.0
        raw.extend(local);scale_diagnostics.append({"scale":"local_10deg","center_deg":float(center),"exposure":exposure,**diagnostics})
    calibrated=[];excluded_too_large=0;excluded_support=0
    for candidate in raw:
        if int(candidate["member_count"])>int(config.hierarchy_max_candidate_members):excluded_too_large+=1;continue
        supported=np.asarray(candidate["annual_counts"],dtype=int)>=int(config.min_year_events)
        if float(np.mean(supported))<float(config.min_year_support_fraction):excluded_support+=1;continue
        candidate["members"]=[full_index[str(value)] for value in candidate["event_ids"]];candidate["membership_mode"]="crossfit_density_fdr_orbit_refinement";calibrated.append(calibrate_candidate(candidate,candidate["calibration_exposure_by_year"],permutations=int(config.calibration_permutations),seed=int(config.calibration_seed)))
    deduplicated,duplicates_removed=_deduplicate(calibrated,float(config.hierarchy_dedup_jaccard))
    for candidate in deduplicated:
        members=np.asarray(candidate["members"],dtype=int);counts=[int(np.sum(year_array[members]==year)) for year in year_values];candidate["annual_counts"]=counts;candidate["members_by_year"]={str(year):int(count) for year,count in zip(year_values,counts)}
        if candidate.get("fused_hierarchy_methods"):candidate["family_id"]=_family_id("FUSE3",candidate["event_ids"])
        candidate.update(calibrate_candidate(candidate,candidate["calibration_exposure_by_year"],permutations=int(config.calibration_permutations),seed=int(config.calibration_seed)))
    deduplicated,anchor_duplicates_removed=_remove_anchor_duplicates(deduplicated,anchors,float(config.hierarchy_dedup_jaccard));q_values=benjamini_yekutieli_qvalues([float(candidate["calibrated_p_value"]) for candidate in deduplicated])
    for candidate,q_value in zip(deduplicated,q_values.tolist()):candidate["calibrated_q_value"]=float(q_value)
    deduplicated.sort(key=_candidate_order);ranked=[*anchors,*deduplicated]
    for rank,candidate in enumerate(ranked,start=1):candidate["seed_rank"]=int(rank);candidate["global_rank"]=int(rank)
    diagnostics={"pipeline":"acrf_v3_5_anchored_cross_window_recurrent_fusion_with_finite_sample_halo","events":int(len(values)),"years":list(year_values),"raw_candidates":int(len(raw)),"eligible_before_deduplication":int(len(calibrated)),"global_anchor_limit":int(config.global_anchor_count),"global_anchors":int(len(anchors)),"global_anchor_hierarchy":anchor_diagnostics,"deduplicated_refinement_candidates":int(len(deduplicated)),"ranked_candidates":int(len(ranked)),"duplicates_removed":int(duplicates_removed),"anchor_duplicates_removed":int(anchor_duplicates_removed),"excluded_too_large":int(excluded_too_large),"excluded_year_support":int(excluded_support),"target_labels_available_to_method":False,"calibration_correction":config.calibration_correction,"scale_diagnostics":scale_diagnostics}
    return ranked,diagnostics

__all__=["_apply_orbit_gate","generate_multiscale_candidates"]
