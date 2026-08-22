#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
import pandas as pd
from gmn_python_api import data_directory as dd
from gmn_python_api import meteor_trajectory_reader as reader

YEARS=(2025,2026)
MONTH=4
WINDOW=(27.0,47.0)
MAX_CLUSTER_SIZE=300
BASE_SCALES=(3.5,3.0,2.5,2.5)
LON=(2.5,3.5,4.5)
LAT=(2.0,3.0,4.0)
SPEED=(1.5,2.5,3.5)
SOLAR=(1.5,2.5,3.5)
MCS=(6,8,12)
MS=(2,4,6)
HDBSCAN_CORNERS=((6,2),(6,6),(12,2),(12,6))

TARGET_TIMES={
'20250424014938','20250424113355','20250424205212','20250425061734','20250425063625','20250425092149','20250425094115','20250425135239','20250425150758','20250426152659','20250426232357','20250427101726','20250427111229','20250427143535','20250427163849','20250428020357','20250428021707','20250428022950','20250428034614','20250428060958','20250428063243','20250428074446','20250428165803','20250428193144','20250428203753','20250429001847','20250429044016','20250429051626','20250429061607','20250429071025','20250429205604','20250429214658','20250429224526','20250430173153',
'20260423112020','20260423142339','20260423230853','20260424143443','20260424145224','20260424180050','20260425113533','20260425154634','20260425164649','20260425201637','20260426105134','20260426123712','20260426161234','20260427002038','20260427091445','20260427110209','20260427140245','20260427172836','20260427172853','20260427233017','20260427234146','20260428010436','20260428020516','20260428155051','20260429073857','20260429082223','20260429152208','20260429171643','20260430124302'
}
assert len(TARGET_TIMES)==63
TARGET_BY_YEAR={year:{x for x in TARGET_TIMES if x.startswith(str(year))} for year in YEARS}
assert {y:len(v) for y,v in TARGET_BY_YEAR.items()}=={2025:34,2026:29}

BASE_COLUMNS=['unique_trajectory_identifier','beginning_utc_time','iau_code','sol_lon_deg','lamgeo_deg','betgeo_deg','vgeo_km_s','medianfiterr_arcsec','num_stat']


def circ_diff(a,b):
    return (np.asarray(a,dtype=float)-np.asarray(b,dtype=float)+180.0)%360.0-180.0


def circ_center(values):
    r=np.radians(np.asarray(values,dtype=float))
    return float(np.degrees(np.arctan2(np.sin(r).mean(),np.cos(r).mean()))%360.0)


def shower_label(v):
    if pd.isna(v): return 'SPORADIC'
    s=str(v).strip().upper()
    if s.endswith('.0') and s[:-2].isdigit(): s=s[:-2]
    return 'SPORADIC' if s in {'','-1','0','...','NONE','NAN','SPO','SPORADIC'} else s


def timestamp_key(v):
    t=pd.to_datetime(v,errors='coerce',utc=True)
    if pd.isna(t): return ''
    return t.strftime('%Y%m%d%H%M%S')


def load_year(year:int)->pd.DataFrame:
    key=f'{year}-{MONTH:02d}'
    print('download',key,flush=True)
    raw=reader.read_data(dd.get_monthly_file_content_by_date(key),output_camel_case=True).reset_index(drop=False)
    missing=[c for c in BASE_COLUMNS if c not in raw.columns]
    if missing: raise RuntimeError(f'{key} missing {missing}')
    d=raw[BASE_COLUMNS].copy()
    d['label']=d['iau_code'].map(shower_label)
    for c in ['sol_lon_deg','lamgeo_deg','betgeo_deg','vgeo_km_s','medianfiterr_arcsec','num_stat']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    good=np.isfinite(d[['sol_lon_deg','lamgeo_deg','betgeo_deg','vgeo_km_s']]).all(axis=1)
    good &= d['sol_lon_deg'].between(0,360) & d['lamgeo_deg'].between(0,360)
    good &= d['betgeo_deg'].between(-90,90) & d['vgeo_km_s'].between(5,75)
    good &= d['num_stat'].fillna(0)>=2
    good &= d['medianfiterr_arcsec'].fillna(9999)<=180
    d=d.loc[good & (d['label']=='SPORADIC')].copy()
    d['tkey']=d['beginning_utc_time'].map(timestamp_key)
    d=d.loc[d['tkey']!=''].copy()
    d=d.sort_values(['tkey','medianfiterr_arcsec','num_stat'],ascending=[True,True,False]).drop_duplicates('tkey',keep='first')
    d=d.loc[d['sol_lon_deg'].between(WINDOW[0],WINDOW[1])].copy().reset_index(drop=True)
    d['year']=year
    print(year,'local quality sporadics',len(d),'targets present',sum(x in TARGET_TIMES for x in d.tkey),flush=True)
    return d


def periodic6(d:pd.DataFrame,scales:tuple[float,float,float,float])->np.ndarray:
    solar=d['sol_lon_deg'].to_numpy(float)
    rel=circ_diff(d['lamgeo_deg'].to_numpy(float),solar)
    off=circ_diff(solar,circ_center(solar))
    lonr=np.radians(rel); solr=np.radians(off)
    lons=180.0/(np.pi*scales[0]); sols=180.0/(np.pi*scales[3])
    return np.column_stack([np.cos(solr)*sols,np.sin(solr)*sols,np.cos(lonr)*lons,np.sin(lonr)*lons,d['betgeo_deg'].to_numpy(float)/scales[1],d['vgeo_km_s'].to_numpy(float)/scales[2]])


def grid():
    settings={}
    def add(scales,mcs,ms,src):
        k=tuple(map(float,scales))+(int(mcs),int(ms))
        settings.setdefault(k,set()).add(src)
    for s in itertools.product(LON,LAT,SPEED,SOLAR): add(s,8,4,'scale_factorial')
    for mcs,ms in itertools.product(MCS,MS): add(BASE_SCALES,mcs,ms,'hdbscan_factorial')
    for s in itertools.product((LON[0],LON[-1]),(LAT[0],LAT[-1]),(SPEED[0],SPEED[-1]),(SOLAR[0],SOLAR[-1])):
        for mcs,ms in HDBSCAN_CORNERS: add(s,mcs,ms,'joint_extreme_interactions')
    out=[]
    for k in sorted(settings):
        out.append({'scales':list(k[:4]),'min_cluster_size':k[4],'min_samples':k[5],'sources':sorted(settings[k])})
    assert len(out)==153,len(out)
    return out


def metrics(ids:set[str])->dict[str,Any]:
    overlap=ids&TARGET_TIMES
    p=len(overlap)/len(ids) if ids else 0.0
    r=len(overlap)/len(TARGET_TIMES)
    f=2*p*r/(p+r) if p+r else 0.0
    return {'reported':len(ids),'overlap':len(overlap),'precision':p,'recall':r,'f1':f,'overlap_2025':len(overlap&TARGET_BY_YEAR[2025]),'overlap_2026':len(overlap&TARGET_BY_YEAR[2026])}


def evaluate(index,setting,d):
    scales=tuple(setting['scales']); X=periodic6(d,scales)
    candidates=[]
    for method_order,method in enumerate(('eom','leaf')):
        model=hdbscan.HDBSCAN(min_cluster_size=int(setting['min_cluster_size']),min_samples=int(setting['min_samples']),metric='euclidean',cluster_selection_method=method,cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False,core_dist_n_jobs=-1).fit(X)
        for label in sorted(int(x) for x in np.unique(model.labels_) if int(x)>=0):
            idx=np.flatnonzero(model.labels_==label)
            if len(idx)>MAX_CLUSTER_SIZE: continue
            years=set(d.iloc[idx]['year'].astype(int).tolist())
            if years!=set(YEARS): continue
            ids=set(d.iloc[idx]['tkey'].astype(str))
            m=metrics(ids)
            if m['overlap']==0: continue
            candidates.append((m['f1'],m['overlap'],m['precision'],-m['reported'],-method_order,method,label,m))
    row={'setting_index':index,'grid_sources':'+'.join(setting['sources']),'lon_scale_deg':scales[0],'lat_scale_deg':scales[1],'speed_scale_km_s':scales[2],'solar_scale_deg':scales[3],'min_cluster_size':int(setting['min_cluster_size']),'min_samples':int(setting['min_samples']),'tracked':False,'selection_method':None,'cluster_label':None,'reported':0,'overlap':0,'precision':0.0,'recall':0.0,'f1':0.0,'overlap_2025':0,'overlap_2026':0}
    if not candidates: return row
    candidates.sort(reverse=True)
    *_,method,label,m=candidates[0]
    row.update({'tracked':True,'selection_method':method,'cluster_label':int(label),**m})
    return row


def run_shard(out:Path,shard_index:int,shard_count:int):
    g=grid(); chosen=[(i,s) for i,s in enumerate(g) if i%shard_count==shard_index]
    d=pd.concat([load_year(y) for y in YEARS],ignore_index=True)
    observed=set(d.tkey)&TARGET_TIMES
    if observed!=TARGET_TIMES:
        missing=sorted(TARGET_TIMES-observed)
        raise RuntimeError(f'quality/local pool missing {len(missing)} canonical discovery-period targets: {missing[:10]}')
    rows=[]
    for j,(i,s) in enumerate(chosen,1):
        print(f'cell {i} ({j}/{len(chosen)}) scales={s["scales"]} mcs={s["min_cluster_size"]} ms={s["min_samples"]}',flush=True)
        r=evaluate(i,s,d); rows.append(r)
        print(' result',r['selection_method'],r['overlap'],'/63 N',r['reported'],'F1',f"{r['f1']:.4f}",flush=True)
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out/f'cells_shard{shard_index}.csv',index=False)
    (out/f'cells_shard{shard_index}.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')


def aggregate(inputs:list[Path],out:Path):
    files=[]
    for p in inputs:
        files.extend(sorted(p.rglob('cells_shard*.csv'))) if p.is_dir() else files.append(p)
    frame=pd.concat([pd.read_csv(p) for p in files],ignore_index=True).drop_duplicates('setting_index').sort_values('setting_index')
    if len(frame)!=153 or set(frame.setting_index.astype(int))!=set(range(153)): raise RuntimeError(f'need 153 cells, got {len(frame)}')
    baseline=frame[(frame.lon_scale_deg==3.5)&(frame.lat_scale_deg==3.0)&(frame.speed_scale_km_s==2.5)&(frame.solar_scale_deg==2.5)&(frame.min_cluster_size==8)&(frame.min_samples==4)]
    if len(baseline)!=1: raise RuntimeError('baseline missing')
    summary={'stage':'orbittrace_acrf_hdbscan_core_posthoc_sensitivity','unique_cells':153,'raw_design_cells':154,'baseline':baseline.iloc[0].to_dict(),'thresholds':{},'selection_method_counts':frame.selection_method.value_counts(dropna=False).to_dict(),'grid_breakdown':{}}
    for n in (63,60,57,50):
        summary['thresholds'][f'at_least_{n}_of_63']={'cells':int((frame.overlap>=n).sum()),'fraction':float((frame.overlap>=n).mean())}
    summary['overlap_quantiles']={str(q):float(frame.overlap.quantile(q)) for q in (0,0.25,0.5,0.75,1)}
    summary['f1_quantiles']={str(q):float(frame.f1.quantile(q)) for q in (0,0.25,0.5,0.75,1)}
    for src in ('scale_factorial','hdbscan_factorial','joint_extreme_interactions'):
        sub=frame[frame.grid_sources.astype(str).str.contains(src,regex=False)]
        summary['grid_breakdown'][src]={'cells':len(sub),'exact_63_fraction':float((sub.overlap==63).mean()),'at_least_60_fraction':float((sub.overlap>=60).mean()),'at_least_57_fraction':float((sub.overlap>=57).mean()),'median_overlap':float(sub.overlap.median()),'min_overlap':int(sub.overlap.min()),'max_overlap':int(sub.overlap.max()),'median_f1':float(sub.f1.median())}
    out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'clustering_sensitivity_cells.csv',index=False)
    (out/'clustering_sensitivity_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True,default=lambda x: x.item() if hasattr(x,'item') else str(x))+'\n')
    lines=['# OrbitTrace ACRF/HDBSCAN core sensitivity','', 'Post-hoc robustness only; no parameter setting was selected from this grid.','',f"- Unique settings: **153** (154 raw design cells; baseline duplicated across two factorials)",f"- Baseline tracked overlap: **{int(baseline.iloc[0].overlap)}/63**, N={int(baseline.iloc[0].reported)}, F1={baseline.iloc[0].f1:.3f}"]
    for n in (63,60,57,50):
        x=summary['thresholds'][f'at_least_{n}_of_63']; lines.append(f"- >= {n}/63: **{x['cells']}/153 ({x['fraction']:.1%})**")
    lines+=['','## Grid breakdown','']
    for src,x in summary['grid_breakdown'].items():
        lines += [f'### {src}','',f"- cells: {x['cells']}",f"- exact 63/63: {x['exact_63_fraction']:.1%}",f"- >=60/63: {x['at_least_60_fraction']:.1%}",f"- >=57/63: {x['at_least_57_fraction']:.1%}",f"- overlap median/range: {x['median_overlap']:.1f} / {x['min_overlap']}-{x['max_overlap']}",f"- median F1: {x['median_f1']:.3f}",'']
    (out/'CLUSTERING_SENSITIVITY.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True,default=str),flush=True)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--shard-index',type=int); ap.add_argument('--shard-count',type=int); ap.add_argument('--aggregate',nargs='*',type=Path); a=ap.parse_args()
    if a.aggregate is not None: aggregate(a.aggregate,a.out); return
    if a.shard_index is None or a.shard_count is None: ap.error('need shard args')
    run_shard(a.out,a.shard_index,a.shard_count)

if __name__=='__main__': main()
