#!/usr/bin/env python3
"""Anonymous server-side census of old-era clean 5XMM-DR15 sources.
No source identifiers, coordinates, or names are returned."""
from pathlib import Path
import io,json,urllib.parse,urllib.request
from astropy.table import Table
OUT=Path('results/xmm_dr15_anonymous_census.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
CUTOFF=60309.99999  # 2023-12-31 UTC approx MJD
BASE=f"sum_flag < 3 AND extent = 0 AND end_time <= {CUTOFF} AND ep_det_ml >= 15"
def q(adql):
    b=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':adql}).encode()
    req=urllib.request.Request(EP,data=b,headers={'User-Agent':'ISEF-XMM-anon-census/1.1','Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req,timeout=60) as r:raw=r.read()
    txt=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in txt[:5000] and 'value="ERROR"' in txt[:5000]:raise RuntimeError(txt[:3000])
    return Table.read(io.BytesIO(raw),format='votable')
def count(extra='1=1'):
    t=q(f"SELECT COUNT(*) AS n FROM xmmssc WHERE {BASE} AND ({extra})")
    return int(t['n'][0])
def main():
    tests={
      'parent':'1=1',
      'single_observation':'n_obs = 1',
      'multi_observation':'n_obs > 1',
      'very_soft_hr3':'pn_hr3 < -0.78',
      'very_soft_hr3_no_gaia':'pn_hr3 < -0.78 AND gaia_match_prob IS NULL',
      'very_soft_hr3_no_wise':'pn_hr3 < -0.78 AND wise_match_prob IS NULL',
      'very_soft_hr3_no_gaia_no_wise':'pn_hr3 < -0.78 AND gaia_match_prob IS NULL AND wise_match_prob IS NULL',
      'classx_outlier_ge5':'classx_outlier >= 5',
      'classx_outlier_ge8':'classx_outlier >= 8',
      'classx_outlier_ge5_no_gaia_no_wise':'classx_outlier >= 5 AND gaia_match_prob IS NULL AND wise_match_prob IS NULL',
      'spec_good':'spec_flag_pl = 0',
      'spec_good_gamma_soft':'spec_flag_pl = 0 AND spec_gamma_pl >= 2.7',
      'spec_good_gamma_hard':'spec_flag_pl = 0 AND spec_gamma_pl <= 1.3',
      # Spec_NH_Pl is stored in cm^-2, not in 1e22 cm^-2 units.
      'spec_good_low_nh':'spec_flag_pl = 0 AND spec_nh_pl <= 3e20',
      'spec_good_high_nh':'spec_flag_pl = 0 AND spec_nh_pl >= 3e22',
      'var_ge5':'approx_source_var >= 5',
      'var_ge30':'approx_source_var >= 30',
      'var_ge100':'approx_source_var >= 100',
      'soft_and_outlier':'pn_hr3 < -0.78 AND classx_outlier >= 5',
      'soft_counterpart_free_and_outlier':'pn_hr3 < -0.78 AND gaia_match_prob IS NULL AND wise_match_prob IS NULL AND classx_outlier >= 5'
    }
    out={'success':True,'base':BASE,'counts':{},'notes':['spec_nh_pl thresholds are cm^-2']}
    for k,v in tests.items():
      try:out['counts'][k]=count(v)
      except Exception as e:out['counts'][k]={'error':f'{type(e).__name__}: {e}'}
    try:
      t=q(f"SELECT TOP 200 pn_hr1,pn_hr2,pn_hr3,pn_hr4,classx_outlier,approx_source_var,spec_gamma_pl,spec_nh_pl,gaia_match_prob,wise_match_prob,n_obs,n_contrib FROM xmmssc WHERE {BASE} ORDER BY classx_outlier DESC")
      import numpy as np
      sm={}
      for c in t.colnames:
        try:
          a=np.asarray(t[c],dtype=float);a=a[np.isfinite(a)]
          if len(a):sm[c]={'n':int(len(a)),'median':float(np.median(a)),'q10':float(np.quantile(a,.1)),'q90':float(np.quantile(a,.9)),'min':float(np.min(a)),'max':float(np.max(a))}
        except:pass
      out['top200_outlier_distribution']=sm
    except Exception as e:out['top200_error']=f'{type(e).__name__}: {e}'
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
