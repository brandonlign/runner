#!/usr/bin/env python3
"""Frozen independent-network replication for DTb68bb6b678e43478."""
from __future__ import annotations

import argparse
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.stats import fisher_exact

SOL0 = 316.185573
SLON0 = 144.84784445604302
BETA0 = -53.00940285307881
VG0 = 14.934766201039407
SLON_SLOPE = -0.5719447594651568
BETA_SLOPE = 0.37813787817134115
VG_SLOPE = -0.33737201749209544
SCALES = np.asarray([3.5, 3.0, 2.5], dtype=float)
ACTIVITY_MIN = 313.310424
ACTIVITY_MAX = 318.766604
ACTIVITY_CENTER = (ACTIVITY_MIN + ACTIVITY_MAX) / 2.0
ACTIVITY_WIDTH = ACTIVITY_MAX - ACTIVITY_MIN
SEASON_HALF = 18.0
ORBIT0 = np.asarray([0.601806, 0.947145, 17.518079, 26.456307, 136.215206], dtype=float)
ORBIT_MEMBER_D = 0.15
SHIFT_STEP = 0.25

SONOTACO_URL = "https://www.astro.sk/iaumdcDB/public/data/SNMv3/{yy:03d}a.zip"
EDMOND_URL = "https://meteornews.net/assets/2025-03-29-edmond-database/U2_{year}_EDM.zip"


def circ_diff(a: Any, b: Any) -> np.ndarray:
    return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float) + 180.0) % 360.0 - 180.0


def equatorial_to_ecliptic(ra_deg: np.ndarray, dec_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ra = np.deg2rad(np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    eps = math.radians(23.43928)
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    xe = x
    ye = y * math.cos(eps) + z * math.sin(eps)
    ze = -y * math.sin(eps) + z * math.cos(eps)
    return np.rad2deg(np.arctan2(ye, xe)) % 360.0, np.rad2deg(np.arcsin(np.clip(ze, -1.0, 1.0)))


def d_sh_matrix(left: np.ndarray, right: np.ndarray | None = None) -> np.ndarray:
    a = np.asarray(left, dtype=float)
    b = a if right is None else np.asarray(right, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1 = np.deg2rad(a[:, 2])[:, None]
    i2 = np.deg2rad(b[:, 2])[None, :]
    dn = (np.deg2rad(a[:, 4])[:, None] - np.deg2rad(b[:, 4])[None, :] + np.pi) % (2*np.pi) - np.pi
    cos_i = np.clip(np.cos(i1)*np.cos(i2) + np.sin(i1)*np.sin(i2)*np.cos(dn), -1.0, 1.0)
    plane = np.arccos(cos_i)
    denom = np.maximum(np.cos(plane/2.0), np.finfo(float).eps)
    common = np.cos((i1+i2)/2.0) * np.sin(dn/2.0) / denom
    dpi = (np.deg2rad(a[:, 3])[:, None] - np.deg2rad(b[:, 3])[None, :] + 2*np.arcsin(np.clip(common,-1,1)) + np.pi) % (2*np.pi) - np.pi
    em = (e1+e2)/2.0
    d2 = (e1-e2)**2 + (q1-q2)**2 + (2*np.sin(plane/2.0))**2 + (em*2*np.sin(dpi/2.0))**2
    return np.sqrt(np.maximum(d2,0.0))


def normalize_orbit_representation(sol: np.ndarray, orbits: np.ndarray) -> tuple[np.ndarray, int]:
    out = np.asarray(orbits, dtype=float).copy()
    # The transformation Omega->Omega+180, omega->omega+180 represents the
    # same physical line of apsides under the opposite node convention. Choose
    # the form whose node is closer to the frozen GMN medoid node.
    direct = np.abs(circ_diff(out[:, 4], ORBIT0[4]))
    flipped_node = (out[:, 4] + 180.0) % 360.0
    flipped = np.abs(circ_diff(flipped_node, ORBIT0[4])) < direct
    out[flipped, 4] = flipped_node[flipped]
    out[flipped, 3] = (out[flipped, 3] + 180.0) % 360.0
    return out, int(flipped.sum())


def read_zip_csv(url: str) -> tuple[pd.DataFrame, str, int]:
    r = requests.get(url, timeout=240)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.csv') and '__note' not in n.lower() and not n.startswith('__MACOSX/')]
        if not names:
            raise RuntimeError(f"no CSV in {url}")
        member = names[0]
        raw = z.read(member)
    return pd.read_csv(io.BytesIO(raw), low_memory=False), member, len(r.content)


def canonical_frame(sol, ra, dec, vg, e, q, inc, peri, node, identifiers, year, source) -> tuple[pd.DataFrame, int]:
    sol = np.asarray(sol, dtype=float)
    ra = np.asarray(ra, dtype=float)
    dec = np.asarray(dec, dtype=float)
    lon, beta = equatorial_to_ecliptic(ra, dec)
    orbits = np.column_stack([e,q,inc,peri,node]).astype(float)
    orbits, flipped = normalize_orbit_representation(sol, orbits)
    frame = pd.DataFrame({
        'sol':sol, 'ra':ra, 'dec':dec, 'slon':circ_diff(lon,sol), 'beta':beta, 'vg':np.asarray(vg,float),
        'e':orbits[:,0], 'q':orbits[:,1], 'inc':orbits[:,2], 'peri':orbits[:,3], 'node':orbits[:,4],
        'identifier':np.asarray(identifiers).astype(str), 'year':int(year), 'source':source,
    })
    arr = frame[['sol','slon','beta','vg','e','q','inc','peri','node']].to_numpy(float)
    valid = np.isfinite(arr).all(axis=1)
    valid &= (frame['vg'].to_numpy(float)>=5)&(frame['vg'].to_numpy(float)<=75)
    valid &= (frame['e'].to_numpy(float)>=0)&(frame['e'].to_numpy(float)<1.5)
    valid &= (frame['q'].to_numpy(float)>0)&(frame['q'].to_numpy(float)<2)
    valid &= (frame['inc'].to_numpy(float)>=0)&(frame['inc'].to_numpy(float)<=180)
    valid &= np.abs(circ_diff(frame['sol'].to_numpy(float),SOL0)) <= SEASON_HALF
    return frame.loc[valid].reset_index(drop=True), flipped


def load_sonotaco(year: int) -> tuple[pd.DataFrame, dict[str,Any]]:
    url = SONOTACO_URL.format(yy=year % 1000)
    raw, member, nbytes = read_zip_csv(url)
    req=['day(UT)','time(UT)','sol(deg)','ra(deg)','de(deg)','vg(km/s)','q(AU)','e','peri(deg)','node(deg)','incl(deg)']
    missing=[x for x in req if x not in raw.columns]
    if missing: raise RuntimeError(f"missing {missing}")
    frame, flipped = canonical_frame(
        pd.to_numeric(raw['sol(deg)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['ra(deg)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['de(deg)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['vg(km/s)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['e'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['q(AU)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['incl(deg)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['peri(deg)'],errors='coerce').to_numpy(float),
        pd.to_numeric(raw['node(deg)'],errors='coerce').to_numpy(float),
        (raw['day(UT)'].astype(str).str.strip()+'T'+raw['time(UT)'].astype(str).str.strip()).to_numpy(),
        year,'SonotaCo')
    return frame, {'url':url,'zip_member':member,'archive_bytes':nbytes,'raw_rows':int(len(raw)),'valid_season_rows':int(len(frame)),'node_forms_flipped':flipped}


def load_edmond(year: int) -> tuple[pd.DataFrame, dict[str,Any]]:
    url=EDMOND_URL.format(year=year)
    raw, member, nbytes=read_zip_csv(url)
    req=['_#','_sol','_ra_t','_dc_t','_vg','_q','_e','_peri','_node','_incl']
    missing=[x for x in req if x not in raw.columns]
    if missing: raise RuntimeError(f"missing {missing}")
    frame, flipped=canonical_frame(
        pd.to_numeric(raw['_sol'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_ra_t'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_dc_t'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_vg'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_e'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_q'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_incl'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_peri'],errors='coerce').to_numpy(float),pd.to_numeric(raw['_node'],errors='coerce').to_numpy(float),raw['_#'].astype(str).to_numpy(),year,'EDMOND')
    return frame, {'url':url,'zip_member':member,'archive_bytes':nbytes,'raw_rows':int(len(raw)),'valid_season_rows':int(len(frame)),'node_forms_flipped':flipped}


def geometry(frame: pd.DataFrame) -> dict[str,np.ndarray]:
    delta=circ_diff(frame['sol'].to_numpy(float),SOL0)
    pred_s=SLON0+SLON_SLOPE*delta
    pred_b=BETA0+BETA_SLOPE*delta
    pred_v=VG0+VG_SLOPE*delta
    r2=(circ_diff(frame['slon'].to_numpy(float),pred_s)/SCALES[0])**2+((frame['beta'].to_numpy(float)-pred_b)/SCALES[1])**2+((frame['vg'].to_numpy(float)-pred_v)/SCALES[2])**2
    inside=(frame['sol'].to_numpy(float)>=ACTIVITY_MIN)&(frame['sol'].to_numpy(float)<=ACTIVITY_MAX)
    orbit=frame[['e','q','inc','peri','node']].to_numpy(float)
    d0=d_sh_matrix(orbit,ORBIT0[None,:])[:,0]
    return {'delta':delta,'r2':r2,'inside':inside,'local':r2<=36.0,'core':r2<=4.0,'d0':d0,'member':inside&(r2<=4.0)&(d0<=ORBIT_MEMBER_D)}


def summarize(frames: list[pd.DataFrame], source: str) -> tuple[dict[str,Any],pd.DataFrame]:
    if not frames:
        return {'source':source,'passed':False,'reason':'no_usable_archives'}, pd.DataFrame()
    frame=pd.concat(frames,ignore_index=True,sort=False)
    g=geometry(frame)
    local=g['local']; core=g['core']; inside=g['inside']
    a=int(np.sum(local&core&inside)); b=int(np.sum(local&~core&inside)); c=int(np.sum(local&core&~inside)); dd=int(np.sum(local&~core&~inside))
    odds,p=fisher_exact([[a,b],[c,dd]],alternative='greater')
    observed_den=int(np.sum(local&inside)); observed_ratio=a/observed_den if observed_den else 0.0
    controls=[]
    min_off=-SEASON_HALF+ACTIVITY_WIDTH/2.0
    max_off=SEASON_HALF-ACTIVITY_WIDTH/2.0
    for off in np.arange(min_off,max_off+1e-9,SHIFT_STEP):
        center=(SOL0+off)%360.0
        if abs(float(circ_diff(center,ACTIVITY_CENTER))) <= ACTIVITY_WIDTH:
            continue
        inwin=np.abs(circ_diff(frame['sol'].to_numpy(float),center)) <= ACTIVITY_WIDTH/2.0
        den=int(np.sum(local&inwin))
        if den<5: continue
        num=int(np.sum(local&core&inwin))
        controls.append({'offset_deg':float(off),'core':num,'local':den,'ratio':num/den})
    shift_p=(1+sum(x['ratio']>=observed_ratio for x in controls))/(1+len(controls)) if controls else 1.0
    members=frame.loc[g['member']].copy()
    member_d0=g['d0'][g['member']]
    years=members['year'].value_counts().sort_index()
    active_years=int(sum(int(v)>=2 for v in years.values))
    if len(members)>=2:
        orb=members[['e','q','inc','peri','node']].to_numpy(float)
        mat=d_sh_matrix(orb)
        medeach=np.median(mat,axis=1); medidx=int(np.argmin(medeach)); to_med=mat[medidx]
        internal_median=float(np.median(to_med)); internal_q90=float(np.quantile(to_med,0.90))
    elif len(members)==1:
        internal_median=internal_q90=0.0
    else:
        internal_median=internal_q90=None
    frozen_med=float(np.median(member_d0)) if len(member_d0) else None
    frozen_q90=float(np.quantile(member_d0,0.90)) if len(member_d0) else None
    passed=bool(len(members)>=8 and active_years>=2 and p<=0.01 and shift_p<=0.05 and internal_median is not None and internal_median<=0.12 and internal_q90<=0.22 and frozen_med is not None and frozen_med<=0.12)
    result={'source':source,'rows':int(len(frame)),'members':int(len(members)),'member_counts_by_year':{str(int(k)):int(v) for k,v in years.items()},'active_years_ge2':active_years,'activity':{'table':[[a,b],[c,dd]],'odds_ratio':float(odds),'p':float(p),'observed_core':a,'observed_local':observed_den,'observed_ratio':float(observed_ratio)},'shifted_windows':{'controls':len(controls),'empirical_p':float(shift_p),'q95_ratio':float(np.quantile([x['ratio'] for x in controls],0.95)) if controls else None,'top':sorted(controls,key=lambda x:x['ratio'],reverse=True)[:10]},'orbit':{'internal_median_d_sh':internal_median,'internal_q90_d_sh':internal_q90,'median_d_sh_to_frozen':frozen_med,'q90_d_sh_to_frozen':frozen_q90},'passed':passed}
    return result,members


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--source',choices=['sonotaco','edmond'],required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    if args.source=='sonotaco': years=range(2007,2026); loader=load_sonotaco; label='SonotaCo'
    else: years=range(2011,2025); loader=load_edmond; label='EDMOND'
    frames=[]; metadata={}
    for y in years:
        try:
            print(f'Downloading {label} {y}',flush=True); f,m=loader(y); frames.append(f); metadata[str(y)]=m; print(f'  usable season rows={len(f):,}',flush=True)
        except Exception as exc:
            metadata[str(y)]={'error':f'{type(exc).__name__}: {exc}'}; print(f'  ERROR {exc}',flush=True)
    result,members=summarize(frames,label)
    payload={'stage':'dtb68_external_replication_v1','scientific_protocol':'orbittrace-raw/pipeline/discovery_search/DTB68_EXTERNAL_REPLICATION_PROTOCOL.md','frozen_lead':'DTb68bb6b678e43478','source_result':result,'downloads':metadata}
    (args.out/f'dtb68_{args.source}.json').write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8')
    if len(members): members.to_csv(args.out/f'dtb68_{args.source}_members.csv',index=False)
    lines=['# DTb68 independent replication: '+label,'',f"Members: **{result.get('members',0)}**. Formal pass: **{result.get('passed',False)}**.",'',f"Counts by year: `{result.get('member_counts_by_year',{})}`",'',f"Activity Fisher p: `{result.get('activity',{}).get('p')}`; shifted-window p: `{result.get('shifted_windows',{}).get('empirical_p')}`.",'',f"Orbit: `{result.get('orbit',{})}`."]
    md='\n'.join(lines)+'\n'; (args.out/f'DTB68_{args.source.upper()}.md').write_text(md,encoding='utf-8'); print(md,flush=True); return 0

if __name__=='__main__': raise SystemExit(main())
