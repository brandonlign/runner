#!/usr/bin/env python3
"""Parallel-network execution of the already-frozen exact v6 LCO gate.

Scientific selection, source ordering, Monte Carlo seeds, NFW necessary screen,
and all six final conditions are unchanged. Only independent Gaia TAP batches
and SDSS SkyServer visit-query batches are fetched concurrently, then merged
by identifier; candidate iteration order remains the original summary order.
"""
import importlib.util, io, json, time, urllib.parse, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from astropy.table import Table

spec=importlib.util.spec_from_file_location('v6','isef/sdss_dr20_lco_final_anonymous_gate_v6_nfw.py')
v6=importlib.util.module_from_spec(spec); spec.loader.exec_module(v6)
ns=v6.ns
g=ns['g']
SQL=ns['SQL']


def _gaia_batch(batch):
    fields='source_id,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_params_solved,visibility_periods_used,astrometric_excess_noise,duplicated_source,ipd_frac_multi_peak,ipd_gof_harmonic_amplitude,non_single_star'
    q=f"SELECT {fields} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in batch)})"
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
    last=None
    for attempt in range(1,5):
        try:
            req=urllib.request.Request(g.GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-FinalAnonymous-v7/1.0'})
            with urllib.request.urlopen(req,timeout=240) as r: raw=r.read()
            t=Table.read(io.BytesIO(raw),format='votable'); cmap={str(n).lower():n for n in t.colnames}; scol=cmap['source_id']
            out={}
            for row in t:
                sid=int(row[scol]); out[sid]={str(n).lower():row[n] for n in t.colnames if n!=scol}
            return out
        except Exception as e:
            last=e
            if attempt<4: time.sleep(2**attempt)
    raise last


def tap_gaia_parallel(ids):
    batches=[ids[a:a+250] for a in range(0,len(ids),250)]
    got={}
    # Conservative concurrency to avoid stressing the public Gaia TAP service.
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs=[ex.submit(_gaia_batch,b) for b in batches]
        for f in as_completed(futs): got.update(f.result())
    return got


def _visit_batch(batch):
    q=("SELECT sdss_id,telescope,xcsao_v_rad,xcsao_e_v_rad,snr,zwarning_flags "
       "FROM mwm_boss_allvisit WHERE telescope='lco25m' AND sdss_id IN ("+
       ','.join(str(int(x)) for x in batch)+")")
    url=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
    last=None
    for attempt in range(1,5):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-FinalAnonymous-v7/1.0'})
            with urllib.request.urlopen(req,timeout=180) as r: obj=json.loads(r.read().decode('utf-8','replace'))
            tables=[x for x in obj if isinstance(x,dict) and x.get('TableName')=='Table1']; rows=tables[0].get('Rows',[]) if tables else []
            out=defaultdict(list); n=0
            for r in rows:
                try:
                    sid=int(r['sdss_id']); rv=float(r['xcsao_v_rad']); er=float(r['xcsao_e_v_rad']); sn=float(r['snr']); zw=int(r['zwarning_flags'])
                    if np.isfinite(rv) and np.isfinite(er) and np.isfinite(sn) and er<30 and sn>10 and zw==0:
                        out[sid].append(rv); n+=1
                except (TypeError,ValueError,KeyError): pass
            return dict(out),n
        except Exception as e:
            last=e
            if attempt<4: time.sleep(2**attempt)
    raise last


def sql_visit_rows_parallel(ids):
    batches=[ids[a:a+200] for a in range(0,len(ids),200)]
    by=defaultdict(list); total=0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(_visit_batch,b) for b in batches]
        for f in as_completed(futs):
            d,n=f.result(); total+=n
            for sid,vals in d.items(): by[sid].extend(vals)
    return by,total

# main()'s function globals are the embedded ns. Replace transport functions only.
ns['tap_gaia']=tap_gaia_parallel
ns['sql_visit_rows']=sql_visit_rows_parallel

if __name__=='__main__':
    ns['main']()
