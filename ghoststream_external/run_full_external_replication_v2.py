#!/usr/bin/env python3
# Authoritative schema-complete rerun.
from __future__ import annotations
import io, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import run_full_external_replication as base


def readzip_v2(raw: bytes):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members=[m for m in archive.namelist() if m.lower().endswith(('.csv','.txt')) and not m.startswith('__MACOSX/')]
        if not members:
            raise RuntimeError('no csv/txt')
        member=max(members,key=lambda q:archive.getinfo(q).file_size)
        data=archive.read(member)
    sample=data[:8192].decode('utf-8-sig',errors='replace')
    first=next((line for line in sample.splitlines() if line.strip()),'')
    if first.count(';')>first.count(','):
        sep=';'; frame=pd.read_csv(io.BytesIO(data),sep=sep,low_memory=False,encoding='utf-8-sig')
    elif first.count(',')>0:
        sep=','; frame=pd.read_csv(io.BytesIO(data),sep=sep,low_memory=False,encoding='utf-8-sig')
    else:
        sep='whitespace'; frame=pd.read_csv(io.BytesIO(data),sep=r'\s+',engine='python',encoding='utf-8-sig')
    frame.columns=[str(column).lstrip('\ufeff').strip() for column in frame.columns]
    return frame,member,sep


def load_edmond(spec: dict, year: int):
    url=spec['url'].format(year=year,yy=year%100)
    raw,meta=base.getzip(url,base.CACHE/'edmond'/f'{year}.zip')
    frame,member,sep=readzip_v2(raw)
    required=['_sol','_elng','_elat','_vg','_e','_q','_incl','_peri','_node']
    missing=[column for column in required if column not in frame.columns]
    if missing:
        raise RuntimeError(f'missing EDMOND fields {missing}; columns={list(frame.columns)}')
    solar=pd.to_numeric(frame['_sol'],errors='coerce').to_numpy(float)
    seasonal=frame.loc[np.abs(base.cd(solar,base.SOL0))<=base.SEASON_HALF_WIDTH].copy()
    identifiers=(seasonal['_#'].astype(str).to_numpy() if '_#' in seasonal.columns
                 else np.asarray([f'EDMOND-{year}-{i}' for i in seasonal.index]))
    out=pd.DataFrame({
        'source':'EDMOND','year':year,'identifier':identifiers,
        'sol':pd.to_numeric(seasonal['_sol'],errors='coerce').to_numpy(float),
        'ecl_lon':pd.to_numeric(seasonal['_elng'],errors='coerce').to_numpy(float)%360.,
        'beta':pd.to_numeric(seasonal['_elat'],errors='coerce').to_numpy(float),
        'vg':pd.to_numeric(seasonal['_vg'],errors='coerce').to_numpy(float),
        'e':pd.to_numeric(seasonal['_e'],errors='coerce').to_numpy(float),
        'q':pd.to_numeric(seasonal['_q'],errors='coerce').to_numpy(float),
        'inc':pd.to_numeric(seasonal['_incl'],errors='coerce').to_numpy(float),
        'peri':pd.to_numeric(seasonal['_peri'],errors='coerce').to_numpy(float)%360.,
        'node':pd.to_numeric(seasonal['_node'],errors='coerce').to_numpy(float)%360.,
    })
    out['sunlon']=base.cd(out.ecl_lon.to_numpy(float),out.sol.to_numpy(float))
    orbits=out[['e','q','inc','peri','node']].to_numpy(float)
    valid=np.isfinite(out[['sol','ecl_lon','beta','vg']]).all(axis=1)
    valid &= out.sol.between(0,360)&out.ecl_lon.between(0,360)&out.beta.between(-90,90)&out.vg.between(5,75)
    valid &= np.isfinite(orbits).all(axis=1)&(orbits[:,0]>=0)&(orbits[:,0]<1.5)&(orbits[:,1]>0)&(orbits[:,1]<2)&(orbits[:,2]>=0)&(orbits[:,2]<=180)
    out=out.loc[valid].reset_index(drop=True)
    meta.update({'member':member,'sep':sep,'raw_rows':len(frame),'seasonal_rows':len(seasonal),'valid_rows':len(out),
                 'schema':'EDMOND native ecliptic radiant and solar-longitude fields'})
    return out,meta


original_load=base.load
base.readzip=readzip_v2

def load_v2(name: str, spec: dict, year: int):
    if name=='EDMOND':
        return load_edmond(spec,year)
    return original_load(name,spec,year)

base.load=load_v2

if __name__=='__main__':
    base.main()
