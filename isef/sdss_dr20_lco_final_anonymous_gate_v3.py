#!/usr/bin/env python3
"""Infrastructure-hardened runner for the already-frozen final anonymous LCO gate.
Scientific rules are unchanged from the frozen gate. This wrapper only:
1) normalizes Gaia TAP returned column names; and
2) makes large SDSS downloads retryable and verifies byte completeness when
   Content-Length is supplied, preventing truncated gzip files from becoming
   pseudo-scientific failures.
"""
import importlib.util, io, os, time, urllib.parse, urllib.request
from pathlib import Path
from astropy.table import Table

spec=importlib.util.spec_from_file_location('gate','isef/sdss_dr20_lco_final_anonymous_gate.py')
gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)


def robust_download(url, p):
    p=Path(p)
    part=Path(str(p)+'.part')
    last=None
    for attempt in range(1,6):
        try:
            if part.exists(): part.unlink()
            req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-FinalAnonymous-v3/1.0'})
            with urllib.request.urlopen(req,timeout=600) as r, open(part,'wb') as f:
                clen=r.headers.get('Content-Length')
                expected=int(clen) if clen and clen.isdigit() else None
                n=0
                while True:
                    b=r.read(8<<20)
                    if not b: break
                    f.write(b); n += len(b)
                f.flush(); os.fsync(f.fileno())
            if expected is not None and n != expected:
                raise EOFError(f'incomplete HTTP body: got {n}, expected {expected}')
            if n <= 0:
                raise EOFError('empty HTTP body')
            part.replace(p)
            return
        except Exception as e:
            last=e
            try:
                if part.exists(): part.unlink()
            except Exception:
                pass
            if attempt < 5:
                time.sleep(2**attempt)
    raise last


def tap_gaia_normalized(ids):
    fields='source_id,pmra,pmra_error,pmdec,pmdec_error,pmra_pmdec_corr,ruwe,astrometric_params_solved,visibility_periods_used,astrometric_excess_noise,duplicated_source,ipd_frac_multi_peak,ipd_gof_harmonic_amplitude,non_single_star'
    got={}
    for a in range(0,len(ids),250):
        batch=ids[a:a+250]
        q=f"SELECT {fields} FROM gaiadr3.gaia_source WHERE source_id IN ({','.join(str(int(x)) for x in batch)})"
        data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
        req=urllib.request.Request(gate.GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-FinalAnonymous-v3/1.0'})
        with urllib.request.urlopen(req,timeout=240) as r: raw=r.read()
        t=Table.read(io.BytesIO(raw),format='votable')
        cmap={str(n).lower():n for n in t.colnames}
        if 'source_id' not in cmap: raise RuntimeError('Gaia TAP source_id column absent')
        scol=cmap['source_id']
        for row in t:
            sid=int(row[scol]); got[sid]={str(n).lower():row[n] for n in t.colnames if n!=scol}
    return got


gate.download=robust_download
gate.tap_gaia=tap_gaia_normalized
if __name__=='__main__': gate.main()
