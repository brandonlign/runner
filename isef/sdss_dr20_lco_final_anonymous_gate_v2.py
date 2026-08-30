#!/usr/bin/env python3
"""Infrastructure-corrected runner for the already-frozen final anonymous LCO gate.
Only Gaia TAP returned-column normalization differs from v1; scientific rules are unchanged.
"""
import importlib.util, io, urllib.parse, urllib.request
from astropy.table import Table

spec=importlib.util.spec_from_file_location('gate','isef/sdss_dr20_lco_final_anonymous_gate.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

def tap_gaia_normalized(ids):
    fields='source_id,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_params_solved,visibility_periods_used,astrometric_excess_noise,duplicated_source,ipd_frac_multi_peak,ipd_gof_harmonic_amplitude,non_single_star'
    got={}
    for a in range(0,len(ids),250):
        batch=ids[a:a+250]
        q=f"SELECT {fields} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in batch)})"
        data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
        req=urllib.request.Request(gate.GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-FinalAnonymous-v2/1.0'})
        with urllib.request.urlopen(req,timeout=240) as r: raw=r.read()
        t=Table.read(io.BytesIO(raw),format='votable')
        cmap={str(n).lower():n for n in t.colnames}
        if 'source_id' not in cmap: raise RuntimeError('Gaia TAP source_id column absent')
        scol=cmap['source_id']
        for row in t:
            sid=int(row[scol]); got[sid]={str(n).lower():row[n] for n in t.colnames if n!=scol}
    return got

gate.tap_gaia=tap_gaia_normalized
if __name__=='__main__': gate.main()
