#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from orbittrace_new_discovery_screen import corrected_allseason_month as base
from orbittrace_new_discovery_screen import drift_track_controls as drift

ECO_REF_SOL = 294.1
ECO_RA = 82.4
ECO_DEC = -34.7
ECO_DRA = 0.76
ECO_DDEC = 0.02
ECO_VG = 16.6
ECO_SOL_MIN = 288.0
ECO_SOL_MAX = 324.0
CORE_ANG = 6.0
SHELL_ANG = 12.0
SPEED_HALF = 3.5

FCM_RA = 101.9
FCM_DEC = -28.1
FCM_VG = 19.5
FCM_SOL_MIN = 325.0
FCM_SOL_MAX = 336.0

DT_SOL_REF = 316.185573
DT_SLON = 144.84784445604302
DT_BETA = -53.00940285307881
DT_VG = 14.934766201039407
DT_SLOPE_SLON = -0.5719447594651568
DT_SLOPE_BETA = 0.37813787817134115
DT_SLOPE_VG = -0.33737201749209544
DT_SOL_MIN = 313.310424
DT_SOL_MAX = 318.766604
DT_SCALES = np.asarray([3.5, 3.0, 2.5], dtype=float)

FROZEN_IDS = {
    2024: {
        "20240204104713_72151","20240204124005_D7tni","20240205061141_NUSiE","20240205144825_XijmX","20240205203257_eOi5z","20240206083516_lTKLd","20240206115530_6iWUH","20240206143826_I2Jyh","20240207102304_l5vnp","20240207121307_jlTJh","20240207122643_lLa8P","20240207132046_H35G2","20240207132046_AAKrb","20240207171100_6GvcK","20240207202314_uW0c3"
    },
    2025: {
        "20250202152021_ePlEe","20250203092514_OJw4k","20250203143516_DrslQ","20250203212327_RyEPF","20250203212332_y4HXa","20250203214120_7mhpf","20250204105604_dmRTl","20250204120318_KZF2n","20250204145506_dADqh","20250205133248_ZJuMV","20250205204427_cuvdz","20250206124059_3saKk","20250206134855_D3XNf","20250207033449_TgkOI","20250207130851_M8JLc"
    },
    2026: {
        "20260203121507_YNZjl","20260203134559_Hs2Wi","20260203135559_O9oWm","20260204103717_abz8b","20260204113213_kp5Ei","20260204113213_CGpN3","20260204120329_jVmac","20260204120330_T80jy","20260205023525_2dF4d","20260205045826_tiUH7","20260205061942_1KJq3","20260205083854_NKGXV","20260205091032_HYxqq","20260205092035_3uV4b","20260205094553_FwFxf","20260205104618_cgR2x","20260205125253_jWkEX","20260206024723_LgUHf","20260206125834_PZwp2","20260206191418_0pRkH","20260206191419_2AGgB","20260206220551_MTzH6","20260206220553_sDCom"
    },
}


def eq_to_ecl(ra_deg: np.ndarray, dec_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ra=np.deg2rad(np.asarray(ra_deg,float)); dec=np.deg2rad(np.asarray(dec_deg,float)); eps=math.radians(23.43928)
    x=np.cos(dec)*np.cos(ra); y=np.cos(dec)*np.sin(ra); z=np.sin(dec)
    xe=x; ye=y*math.cos(eps)+z*math.sin(eps); ze=-y*math.sin(eps)+z*math.cos(eps)
    return np.rad2deg(np.arctan2(ye,xe))%360.0, np.rad2deg(np.arcsin(np.clip(ze,-1,1)))


def ecl_to_eq(lon_deg: np.ndarray, lat_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lon=np.deg2rad(np.asarray(lon_deg,float)); lat=np.deg2rad(np.asarray(lat_deg,float)); eps=math.radians(23.43928)
    x=np.cos(lat)*np.cos(lon); y=np.cos(lat)*np.sin(lon); z=np.sin(lat)
    xe=x; ye=y*math.cos(eps)-z*math.sin(eps); ze=y*math.sin(eps)+z*math.cos(eps)
    return np.rad2deg(np.arctan2(ye,xe))%360.0, np.rad2deg(np.arcsin(np.clip(ze,-1,1)))


def sph_sep(lon1,lat1,lon2,lat2):
    l1=np.deg2rad(lon1); b1=np.deg2rad(lat1); l2=np.deg2rad(lon2); b2=np.deg2rad(lat2)
    c=np.sin(b1)*np.sin(b2)+np.cos(b1)*np.cos(b2)*np.cos(l1-l2)
    return np.rad2deg(np.arccos(np.clip(c,-1,1)))


def med(values) -> float | None:
    arr=pd.to_numeric(pd.Series(values),errors="coerce").to_numpy(float)
    arr=arr[np.isfinite(arr)]
    return None if not len(arr) else float(np.median(arr))


def summaries(data: pd.DataFrame, mask: np.ndarray, ra: np.ndarray, dec: np.ndarray) -> dict[str,Any]:
    idx=np.flatnonzero(mask)
    if not len(idx): return {"count":0,"labels":{},"medians":{}}
    sub=data.iloc[idx]
    labels=Counter(base.code_text(v) or "<SPORADIC>" for v in sub["iau_code"].tolist())
    node=pd.to_numeric(sub["node"],errors="coerce").to_numpy(float)
    sol=pd.to_numeric(sub["sol_lon_deg"],errors="coerce").to_numpy(float)
    node_res=base.circ_diff(node, (sol-180.0)%360.0)
    return {
        "count":int(len(idx)),
        "labels":dict(labels.most_common()),
        "medians":{
            "ra":med(ra[idx]),"dec":med(dec[idx]),"vg":med(sub["vgeo_km_s"]),
            "q":med(sub["q"]),"e":med(sub["e"]),"incl":med(sub["incl"]),"peri":med(sub["peri"]),
            "node_minus_expected":med(node_res),
        }
    }


def load_year(year:int) -> pd.DataFrame:
    frames=[]
    for month in (1,2):
        prepared=drift.prepare_all_quality(base.load_month(year,month),year,month)
        frames.append(prepared["data"])
    data=pd.concat(frames,ignore_index=True).drop_duplicates(subset=["unique_trajectory_identifier"]).reset_index(drop=True)
    sol=data["sol_lon_deg"].to_numpy(float)
    keep=(sol>=ECO_SOL_MIN)&(sol<=FCM_SOL_MAX)
    return data.loc[keep].reset_index(drop=True)


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,required=True); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    year=args.year
    if year not in range(2019,2027): raise SystemExit("year must be 2019..2026")
    args.out.mkdir(parents=True,exist_ok=True)
    data=load_year(year)
    sol=data["sol_lon_deg"].to_numpy(float); lon=data["lamgeo_deg"].to_numpy(float); lat=data["betgeo_deg"].to_numpy(float); vg=data["vgeo_km_s"].to_numpy(float)
    ra,dec=ecl_to_eq(lon,lat)

    eco_ra=(ECO_RA+ECO_DRA*base.circ_diff(sol,ECO_REF_SOL))%360.0
    eco_dec=ECO_DEC+ECO_DDEC*base.circ_diff(sol,ECO_REF_SOL)
    eco_lon,eco_lat=eq_to_ecl(eco_ra,eco_dec)
    eco_sep=sph_sep(lon,lat,eco_lon,eco_lat); eco_dv=np.abs(vg-ECO_VG)
    eco_range=(sol>=ECO_SOL_MIN)&(sol<ECO_SOL_MAX)
    eco_core=eco_range&(eco_sep<=CORE_ANG)&(eco_dv<=SPEED_HALF)
    eco_shell=eco_range&(eco_sep>CORE_ANG)&(eco_sep<=SHELL_ANG)&(eco_dv<=SPEED_HALF)

    dx=base.circ_diff(sol,DT_SOL_REF)
    dt_pred_slon=(DT_SLON+DT_SLOPE_SLON*dx)%360.0; dt_pred_beta=DT_BETA+DT_SLOPE_BETA*dx; dt_pred_vg=DT_VG+DT_SLOPE_VG*dx
    obs_slon=base.circ_diff(lon,sol)%360.0
    dt_r2=(base.circ_diff(obs_slon,dt_pred_slon)/DT_SCALES[0])**2+((lat-dt_pred_beta)/DT_SCALES[1])**2+((vg-dt_pred_vg)/DT_SCALES[2])**2
    dt_core=(sol>=DT_SOL_MIN)&(sol<=DT_SOL_MAX)&(dt_r2<=4.0)

    fcm_lon,fcm_lat=eq_to_ecl(np.full(len(data),FCM_RA),np.full(len(data),FCM_DEC))
    fcm_sep=sph_sep(lon,lat,fcm_lon,fcm_lat); fcm_dv=np.abs(vg-FCM_VG)
    fcm_core=(sol>=FCM_SOL_MIN)&(sol<=FCM_SOL_MAX)&(fcm_sep<=CORE_ANG)&(fcm_dv<=SPEED_HALF)

    area_core=2*math.pi*(1-math.cos(math.radians(CORE_ANG)))
    area_12=2*math.pi*(1-math.cos(math.radians(SHELL_ANG)))
    core_to_shell_area=area_core/(area_12-area_core)
    bins=[]
    for lo in np.arange(ECO_SOL_MIN,ECO_SOL_MAX,2.0):
        hi=lo+2.0; bm=(sol>=lo)&(sol<hi)
        c=int(np.sum(eco_core&bm)); s=int(np.sum(eco_shell&bm)); exp=s*core_to_shell_area
        row=summaries(data,eco_core&bm,ra,dec)
        row.update({"sol_lo":float(lo),"sol_hi":float(hi),"core":c,"shell":s,"area_scaled_shell_expected":float(exp),"density_ratio":None if exp==0 else float(c/exp)})
        bins.append(row)

    ids=data["unique_trajectory_identifier"].astype(str).to_numpy()
    wanted=FROZEN_IDS.get(year,set()); exact=np.asarray([v in wanted for v in ids],bool)
    exact_found=int(exact.sum()); exact_eco=int(np.sum(exact&eco_core)); exact_dt=int(np.sum(exact&dt_core))
    exact_metrics={
        "expected_ids":len(wanted),"found_ids":exact_found,"eco_core":exact_eco,"dt_core":exact_dt,
        "eco_core_fraction":None if exact_found==0 else exact_eco/exact_found,
        "median_eco_sep_deg":med(eco_sep[exact]),"median_eco_speed_delta":med(eco_dv[exact]),
    }

    result={
        "stage":"dtb68_eco_continuity_year_v1","year":year,"rows":len(data),
        "area_core_to_shell":core_to_shell_area,"bins":bins,
        "eco_total":summaries(data,eco_core,ra,dec),"dtb68_tube_total":summaries(data,dt_core,ra,dec),
        "eco_dtb68_overlap":int(np.sum(eco_core&dt_core)),"fcm_side_check":summaries(data,fcm_core,ra,dec),
        "exact_frozen_dtb68_members":exact_metrics,
        "eco_core_events":[{
            "id":str(ids[i]),"sol":float(sol[i]),"ra":float(ra[i]),"dec":float(dec[i]),"vg":float(vg[i]),
            "eco_sep":float(eco_sep[i]),"eco_dv":float(eco_dv[i]),"iau_code":base.code_text(data.iloc[i]["iau_code"]) or "<SPORADIC>",
            "q":base.finite(data.iloc[i]["q"]),"e":base.finite(data.iloc[i]["e"]),"incl":base.finite(data.iloc[i]["incl"]),"peri":base.finite(data.iloc[i]["peri"]),"node":base.finite(data.iloc[i]["node"])
        } for i in np.flatnonzero(eco_core)]
    }
    path=args.out/f"dtb68_eco_continuity_{year}.json"; path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    lines=[f"# DTb68/ECO continuity audit {year}","",f"Quality rows lambda=288..336: **{len(data)}**.",f"ECO core: **{result['eco_total']['count']}**; DTb68 tube: **{result['dtb68_tube_total']['count']}**; overlap: **{result['eco_dtb68_overlap']}**; FCM side core: **{result['fcm_side_check']['count']}**.",f"Exact frozen DTb68 members: `{exact_metrics}`","","| sol bin | ECO core | shell | shell expected | density ratio | labels |","|---|---:|---:|---:|---:|---|"]
    for b in bins:
        ratio="—" if b["density_ratio"] is None else f"{b['density_ratio']:.2f}"
        lines.append(f"| {b['sol_lo']:.0f}-{b['sol_hi']:.0f} | {b['core']} | {b['shell']} | {b['area_scaled_shell_expected']:.2f} | {ratio} | `{b['labels']}` |")
    (args.out/f"DTB68_ECO_CONTINUITY_{year}.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines),flush=True)
    return 0

if __name__=="__main__": raise SystemExit(main())
