#!/usr/bin/env python3
"""External-control extraction pilot for known binary asteroid 6764 Kirillavrov.

This script opens only the known published positive control in historical TESS
Sector 1. It does not query or open any Year-8 discovery-sample light curve.
The purpose is infrastructure validation: can current tess-asteroids v1.5.1
reproduce a usable moving-object light curve in our compute environment?
No scientific detector threshold is chosen from this pilot.
"""
from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np
from astropy.io import fits
from tess_asteroids import MovingTPF, __version__ as tess_asteroids_version

OUT=Path('results/tess_binary_6764_extraction_pilot');OUT.mkdir(parents=True,exist_ok=True)
# Horizons resolves the numbered minor planet robustly by number; the earlier
# combined string "6764 Kirillavrov" was rejected before ephemeris generation.
TARGET='6764';DISPLAY_TARGET='6764 Kirillavrov';SECTOR=1

def table_summary(path):
    with fits.open(path,memmap=False) as h:
        tabs=[]
        for i,hd in enumerate(h):
            if getattr(hd,'data',None) is None or not hasattr(hd.data,'names'):continue
            names=list(hd.data.names or []);row={'hdu':i,'extname':str(hd.header.get('EXTNAME','')),'n':len(hd.data),'columns':names}
            for cand in ['TIME','FLUX','SAP_FLUX','PSF_FLUX','AP_FLUX','QUALITY','TESSMAG','MAG']:
                if cand in names:
                    a=np.asarray(hd.data[cand]);good=np.isfinite(a) if np.issubdtype(a.dtype,np.number) else np.ones(len(a),bool)
                    row[cand]={'finite_n':int(good.sum())}
                    if good.any() and np.issubdtype(a.dtype,np.number):
                        row[cand].update({'min':float(np.nanmin(a)),'median':float(np.nanmedian(a)),'max':float(np.nanmax(a))})
            tabs.append(row)
    return tabs

def main():
    # Let tess-asteroids/Horizons determine the actual Sector-1 camera/CCD. The
    # package raises if the target is not uniquely on one camera/CCD.
    mt=MovingTPF.from_name(TARGET,sector=SECTOR)
    mt.make_tpf(shape=(11,11),bg_method='linear_model',ap_method='prf',save=True,outdir=str(OUT))
    mt.make_lc(method='all',save=True,outdir=str(OUT))
    files=sorted(str(Path(x).name) for x in glob.glob(str(OUT/'*.fits')))
    rep={'role':'known-binary external extraction control only','target':DISPLAY_TARGET,'query_target':TARGET,'sector':SECTOR,
         'tess_asteroids_version':tess_asteroids_version,'year8_discovery_values_opened':False,
         'camera':int(mt.camera),'ccd':int(mt.ccd),'ephemeris_rows':int(len(mt.ephem)),
         'ephem_time_min':float(np.nanmin(mt.ephem['time'])),'ephem_time_max':float(np.nanmax(mt.ephem['time'])),
         'files':files,'fits_tables':{f:table_summary(OUT/f) for f in files}}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rep,indent=2,sort_keys=True))

if __name__=='__main__':main()
