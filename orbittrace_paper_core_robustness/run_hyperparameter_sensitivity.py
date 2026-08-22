#!/usr/bin/env python3
"""Frozen post-hoc ACRF-v3.5 core-hyperparameter robustness grid."""
from __future__ import annotations
import argparse,itertools,json,re
from dataclasses import replace
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader
from pipeline.unified_v2.features import circular_center_deg,circular_difference_deg,periodic_physical6_from_raw
from pipeline.unified_v3.config import V3Config
from pipeline.unified_v3.membership import expand_candidate
from pipeline.unified_v3.method import _apply_orbit_gate,generate_multiscale_candidates

YEARS=(2022,2023,2024,2025,2026);SEED_YEARS=(2025,2026);MONTH=4
TARGET=Path("OrbitTrace_April_95_GMN_timestamps.csv")
BASE_SCALES=(3.5,3.0,2.5,2.5);LON_SCALES=(2.5,3.5,4.5);LAT_SCALES=(2.0,3.0,4.0);SPEED_SCALES=(1.5,2.5,3.5);SOLAR_SCALES=(1.5,2.5,3.5);MCS_LEVELS=(6,8,12);MS_LEVELS=(2,4,6);HDBSCAN_CORNERS=((6,2),(6,6),(12,2),(12,6))
ORBIT_COLUMNS=["e","q_au","i_deg","peri_deg","node_deg"]
SIGMA_COLUMNS=["sigma_9","sigma_15","sigma_10","sigma_11","sigma_12"]
BASE_COLUMNS=["unique_trajectory_identifier","beginning_utc_time","iau_code","sol_lon_deg","lamgeo_deg","betgeo_deg","vgeo_km_s",*ORBIT_COLUMNS,*SIGMA_COLUMNS,"medianfiterr_arcsec","num_stat","participating_stations"]
BASELINE_EXPECTED={"rank":7,"final_member_count":123,"final_overlap":95,"target_count":95,"final_precision":0.7723577235772358,"final_recall":1.0,"final_f1":0.8715596330275228}

def shower_label(value:Any)->str:
    if pd.isna(value):return "SPORADIC"
    text=str(value).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():text=text[:-2]
    return "SPORADIC" if text in {"","-1","0","...","NONE","NAN","SPO","SPORADIC"} else text

def prepare(year:int)->dict[str,Any]:
    key=f"{year}-{MONTH:02d}"; print(f"Downloading {key}",flush=True)
    frame=reader.read_data(dd.get_monthly_file_content_by_date(key),output_camel_case=True).reset_index(drop=False)
    missing=[column for column in BASE_COLUMNS if column not in frame.columns]
    if missing:raise RuntimeError(f"Missing GMN columns: {missing}")
    data=frame[BASE_COLUMNS].copy();data["label"]=data["iau_code"].map(shower_label)
    numeric=["sol_lon_deg","lamgeo_deg","betgeo_deg","vgeo_km_s",*ORBIT_COLUMNS,*SIGMA_COLUMNS,"medianfiterr_arcsec","num_stat"]
    for col in numeric:data[col]=pd.to_numeric(data[col],errors="coerce")
    valid=np.isfinite(data[["sol_lon_deg","lamgeo_deg","betgeo_deg","vgeo_km_s"]]).all(axis=1);valid &= data["sol_lon_deg"].between(0,360)&data["lamgeo_deg"].between(0,360);valid &= data["betgeo_deg"].between(-90,90)&data["vgeo_km_s"].between(5,75);valid &= data["num_stat"].fillna(0)>=2;valid &= data["medianfiterr_arcsec"].fillna(9999)<=180
    data=data.loc[valid&(data["label"]=="SPORADIC")].reset_index(drop=True);quality_rows=len(data)
    if len(data)>150000:data=data.sample(150000,random_state=20260731+year*100+MONTH).sort_index().reset_index(drop=True)
    return {"data":data,"quality_rows":quality_rows}

def feature_panel(data:pd.DataFrame,config:V3Config)->np.ndarray:
    solar=data["sol_lon_deg"].to_numpy(float);raw=np.column_stack((circular_difference_deg(data["lamgeo_deg"].to_numpy(float),solar),data["betgeo_deg"].to_numpy(float),data["vgeo_km_s"].to_numpy(float),circular_difference_deg(solar,circular_center_deg(solar))))
    return periodic_physical6_from_raw(raw,config.feature_scales)

def timestamp_key(value:Any)->str:
    return "".join(character for character in str(value) if character.isdigit())[:14]

def target_keys(years:tuple[int,...])->set[str]:
    frame=pd.read_csv(TARGET);timestamps=pd.to_datetime(frame["Tobs"],format="%Y-%m-%d-%H:%M:%S",errors="coerce")
    return {value.strftime("%Y%m%d%H%M%S") for value in timestamps.dropna() if int(value.year) in years}

def build_grid()->list[dict[str,Any]]:
    settings:dict[tuple[float,float,float,float,int,int],set[str]]={}
    def add(scales,mcs,ms,source):settings.setdefault((*map(float,scales),int(mcs),int(ms)),set()).add(source)
    for scales in itertools.product(LON_SCALES,LAT_SCALES,SPEED_SCALES,SOLAR_SCALES):add(scales,8,4,"scale_factorial")
    for mcs,ms in itertools.product(MCS_LEVELS,MS_LEVELS):add(BASE_SCALES,mcs,ms,"hdbscan_factorial")
    for scales in itertools.product((2.5,4.5),(2.0,4.0),(1.5,3.5),(1.5,3.5)):
        for mcs,ms in HDBSCAN_CORNERS:add(scales,mcs,ms,"joint_extreme_interactions")
    rows=[]
    for key in sorted(settings):
        lon,lat,speed,solar,mcs,ms=key;rows.append({"feature_scales":[lon,lat,speed,solar],"min_cluster_size":mcs,"min_samples":ms,"grid_sources":sorted(settings[key])})
    if len(rows)!=154:raise RuntimeError(f"grid size {len(rows)}")
    return rows

def load_panel()->dict[str,Any]:
    frames=[];year_arrays=[];ids=[];metadata={}
    for year in YEARS:
        prepared=prepare(year);data=prepared["data"].copy();event_ids=data["unique_trajectory_identifier"].astype(str).to_numpy()
        if len(set(event_ids.tolist()))!=len(event_ids):raise RuntimeError(f"Duplicate event IDs in {year}")
        frames.append(data);year_arrays.append(np.full(len(data),year,dtype=np.int64));ids.extend(event_ids.tolist());metadata[str(year)]={"rows":int(len(data)),"quality_rows_before_sampling":int(prepared["quality_rows"])}
    all_data=pd.concat(frames,ignore_index=True,sort=False);years=np.concatenate(year_arrays);event_ids=np.asarray(ids,dtype=str)
    if len(set(event_ids.tolist()))!=len(event_ids):raise RuntimeError("Event IDs not globally unique")
    return {"frames":frames,"years":years,"event_ids":event_ids,"orbit_matrix":all_data[ORBIT_COLUMNS].to_numpy(float),"solar":all_data["sol_lon_deg"].to_numpy(float),"metadata":metadata}

def score_ids(ids,target):
    reported={timestamp_key(value) for value in ids};overlap=len(reported&target);precision=overlap/len(reported) if reported else 0.0;recall=overlap/len(target) if target else 0.0;f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    return {"reported":len(reported),"overlap":overlap,"precision":precision,"recall":recall,"f1":f1}

def evaluate_setting(index,setting,panel,all_target,seed_target):
    scales=tuple(float(x) for x in setting["feature_scales"]);config=replace(V3Config(),feature_scales=scales,min_cluster_size=int(setting["min_cluster_size"]),min_samples=int(setting["min_samples"]));matrix=np.vstack([feature_panel(frame,config) for frame in panel["frames"]]);years=panel["years"];event_ids=panel["event_ids"];seed_mask=np.isin(years,np.asarray(SEED_YEARS,dtype=np.int64))
    candidates,diagnostics=generate_multiscale_candidates(matrix[seed_mask],years[seed_mask],event_ids[seed_mask],panel["solar"][seed_mask],config);tracked=[]
    for candidate in candidates:
        metrics=score_ids(candidate.get("event_ids",[]),seed_target)
        if metrics["overlap"]:tracked.append((metrics["f1"],metrics["overlap"],-int(candidate["global_rank"]),candidate,metrics))
    row={"setting_index":index,"grid_sources":"+".join(setting["grid_sources"]),"lon_scale_deg":scales[0],"lat_scale_deg":scales[1],"speed_scale_km_s":scales[2],"solar_scale_deg":scales[3],"min_cluster_size":config.min_cluster_size,"min_samples":config.min_samples,"ranked_candidate_count":len(candidates),"raw_candidate_count":int(diagnostics.get("raw_candidates",0)),"target_opened_only_after_ranking":True,"materialization_budget":100,"tracked":False,"rank":None,"family_id":None,"hierarchy_method":None,"membership_mode":None,"seed_reported":0,"seed_overlap":0,"seed_precision":0.0,"seed_recall":0.0,"seed_f1":0.0,"within_top100":False,"final_member_count":0,"final_overlap":0,"target_count":len(all_target),"final_precision":0.0,"final_recall":0.0,"final_f1":0.0,**{f"overlap_{y}":0 for y in YEARS}}
    if not tracked:return row
    tracked.sort(key=lambda item:(-item[0],-item[1],-item[2]));_,_,_,candidate,seed_metrics=tracked[0];rank=int(candidate["global_rank"]);row.update({"tracked":True,"rank":rank,"family_id":str(candidate["family_id"]),"hierarchy_method":str(candidate.get("hierarchy_method")),"membership_mode":str(candidate.get("membership_mode")),"seed_reported":seed_metrics["reported"],"seed_overlap":seed_metrics["overlap"],"seed_precision":seed_metrics["precision"],"seed_recall":seed_metrics["recall"],"seed_f1":seed_metrics["f1"],"within_top100":rank<=100})
    if rank>100:return row
    if candidate.get("membership_mode")=="hierarchy_core":final_ids=sorted(map(str,candidate.get("event_ids",[])))
    else:
        full_index={event_id:i for i,event_id in enumerate(event_ids.tolist())};expanded_input=dict(candidate);expanded_input["members"]=[full_index[str(value)] for value in candidate["event_ids"]];expanded=expand_candidate(expanded_input,matrix,years,event_ids,config);gated=_apply_orbit_gate(expanded,panel["orbit_matrix"],event_ids,config);final_ids=sorted(map(str,gated["final_event_ids"]))
    fm=score_ids(final_ids,all_target);final_keys={timestamp_key(v) for v in final_ids};overlap_keys=final_keys&all_target;row.update({"final_member_count":fm["reported"],"final_overlap":fm["overlap"],"final_precision":fm["precision"],"final_recall":fm["recall"],"final_f1":fm["f1"]})
    for y in YEARS:row[f"overlap_{y}"]=sum(v.startswith(str(y)) for v in overlap_keys)
    return row

def baseline_match(row):return row["lon_scale_deg"]==3.5 and row["lat_scale_deg"]==3.0 and row["speed_scale_km_s"]==2.5 and row["solar_scale_deg"]==2.5 and int(row["min_cluster_size"])==8 and int(row["min_samples"])==4

def assert_baseline(row):
    for key,expected in BASELINE_EXPECTED.items():
        observed=row[key]
        if isinstance(expected,float):
            if not np.isclose(float(observed),expected,atol=1e-12,rtol=1e-12):raise RuntimeError(f"Baseline mismatch {key}: {observed} != {expected}")
        elif int(observed) != expected:raise RuntimeError(f"Baseline mismatch {key}: {observed} != {expected}")

def run_shard(out:Path,shard_index:int,shard_count:int)->int:
    grid=build_grid();selected=[(i,row) for i,row in enumerate(grid) if i%shard_count==shard_index];panel=load_panel();all_target=target_keys(YEARS);seed_target=target_keys(SEED_YEARS)
    if len(all_target)!=95 or len(seed_target)!=63:raise RuntimeError("target count mismatch")
    rows=[]
    for pos,(i,setting) in enumerate(selected,1):
        print(f"[{pos}/{len(selected)}] cell={i} {setting}",flush=True);row=evaluate_setting(i,setting,panel,all_target,seed_target);rows.append(row);print(f"RESULT cell={i} rank={row['rank']} overlap={row['final_overlap']}/95 N={row['final_member_count']} F1={row['final_f1']:.4f}",flush=True)
    out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).sort_values("setting_index").to_csv(out/f"hyperparameter_cells_shard{shard_index}.csv",index=False);return 0

def aggregate(inputs:list[Path],out:Path)->int:
    paths=[]
    for p in inputs:paths.extend(sorted(p.rglob("hyperparameter_cells_shard*.csv"))) if p.is_dir() else paths.append(p)
    frame=pd.concat([pd.read_csv(p) for p in paths],ignore_index=True).drop_duplicates(subset=["setting_index"],keep=False).sort_values("setting_index")
    if len(frame)!=154 or set(frame["setting_index"].astype(int))!=set(range(154)):raise RuntimeError(f"Expected 154 cells, found {len(frame)}")
    baseline=[r for r in frame.to_dict(orient="records") if baseline_match(r)]
    if len(baseline)!=1:raise RuntimeError("baseline row missing/duplicated")
    assert_baseline(baseline[0]);tracked=frame[frame["tracked"]==True];top100=tracked[tracked["within_top100"]==True]
    summary={"stage":"acrf_v3_5_frozen_core_hyperparameter_robustness","grid_cells":154,"baseline_reproduced":True,"tracked_cells":int(len(tracked)),"rank_le_100_cells":int(len(top100)),"rank_le_100_fraction":float(len(top100)/154),"exact_95_recovery_cells":int((frame["final_overlap"]==95).sum()),"exact_95_recovery_fraction":float((frame["final_overlap"]==95).mean()),"at_least_90_recovery_cells":int((frame["final_overlap"]>=90).sum()),"at_least_90_recovery_fraction":float((frame["final_overlap"]>=90).mean()),"at_least_80_recovery_cells":int((frame["final_overlap"]>=80).sum()),"at_least_80_recovery_fraction":float((frame["final_overlap"]>=80).mean()),"rank_quantiles_tracked":{str(q):float(tracked["rank"].quantile(q)) if len(tracked) else None for q in (0,.25,.5,.75,1)},"final_overlap_quantiles_all_cells":{str(q):float(frame["final_overlap"].quantile(q)) for q in (0,.25,.5,.75,1)},"member_count_range_top100":[int(top100["final_member_count"].min()) if len(top100) else None,int(top100["final_member_count"].max()) if len(top100) else None],"grid_breakdown":{},"interpretation_rule":"Frozen post-hoc sensitivity; no hyperparameter replacement or tuning."}
    for source in ("scale_factorial","hdbscan_factorial","joint_extreme_interactions"):
        subset=frame[frame["grid_sources"].astype(str).str.contains(source,regex=False)];summary["grid_breakdown"][source]={"cells":int(len(subset)),"rank_le_100_fraction":float((subset["within_top100"]==True).mean()),"exact_95_fraction":float((subset["final_overlap"]==95).mean()),"at_least_90_fraction":float((subset["final_overlap"]>=90).mean()),"at_least_80_fraction":float((subset["final_overlap"]>=80).mean()),"median_final_overlap":float(subset["final_overlap"].median()),"minimum_final_overlap":int(subset["final_overlap"].min()),"maximum_final_overlap":int(subset["final_overlap"].max())}
    out.mkdir(parents=True,exist_ok=True);frame.to_csv(out/"hyperparameter_sensitivity_cells.csv",index=False);(out/"hyperparameter_sensitivity_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    lines=["# ACRF-v3.5 core-hyperparameter robustness","","Frozen post-hoc sensitivity; the selected method was not retuned.","",f"- Cells: **154**",f"- Baseline reproduced exactly: **True**",f"- Rank <=100: **{summary['rank_le_100_cells']}/154 ({summary['rank_le_100_fraction']:.1%})**",f"- Exact 95/95: **{summary['exact_95_recovery_cells']}/154 ({summary['exact_95_recovery_fraction']:.1%})**",f"- >=90/95: **{summary['at_least_90_recovery_cells']}/154 ({summary['at_least_90_recovery_fraction']:.1%})**",f"- >=80/95: **{summary['at_least_80_recovery_cells']}/154 ({summary['at_least_80_recovery_fraction']:.1%})**"]
    (out/"HYPERPARAMETER_ROBUSTNESS.md").write_text("\n".join(lines)+"\n");print("SUMMARY_JSON="+json.dumps(summary,sort_keys=True),flush=True);return 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);ap.add_argument("--shard-index",type=int);ap.add_argument("--shard-count",type=int);ap.add_argument("--aggregate",nargs="*",type=Path);a=ap.parse_args()
    if a.aggregate is not None:return aggregate(a.aggregate,a.out)
    return run_shard(a.out,a.shard_index,a.shard_count)
if __name__=="__main__":raise SystemExit(main())
