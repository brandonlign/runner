#!/usr/bin/env python3
from pathlib import Path
import urllib.parse, urllib.request, io
from astropy.table import Table
import xmm_reprocessing_dev_properties as base

def qbin(lo,hi):
    q=f'''SELECT TOP {base.CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.ep_flux AS flux,s.ep_hr2 AS hr2,s.ep_hr3 AS hr3,s.ep_det_ml AS detml,s.n_contrib AS ncontrib,s.n_obs AS nobs,s.approx_source_var AS svar,d.obsid AS dobsid FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {base.BASE} AND d.pps_srcnum IS NOT NULL AND s.ra >= {lo} AND s.ra < {hi}'''
    t=base.tap(q)
    if len(t)>=base.CAP: raise RuntimeError(f'cap hit {lo}-{hi}')
    return t
base.qbin=qbin
base.OUT=Path('results/xmm_reprocessing_dev_properties_detectiononly.json')
if __name__=='__main__': base.main()
