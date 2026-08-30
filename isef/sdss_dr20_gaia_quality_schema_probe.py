#!/usr/bin/env python3
"""Gaia DR3 TAP schema-only probe for fields required by final high-speed-star astrometric validation.
No source identifiers are queried.
"""
from pathlib import Path
import json, urllib.parse, urllib.request, io
OUT=Path('results/sdss_dr20_gaia_quality_schema_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
END='https://gea.esac.esa.int/tap-server/tap/sync'
def tap(q):
 data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':q}).encode()
 req=urllib.request.Request(END,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-GaiaSchema/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf-8','replace')
out={'success':False,'status':'GAIA_SCHEMA_ONLY','source_rows_accessed':False}
try:
 wanted=['source_id','ra','dec','parallax','parallax_error','pmra','pmra_error','pmdec','pmdec_error','ra_dec_corr','ra_parallax_corr','ra_pmra_corr','ra_pmdec_corr','dec_parallax_corr','dec_pmra_corr','dec_pmdec_corr','parallax_pmra_corr','parallax_pmdec_corr','pmra_pmdec_corr','ruwe','astrometric_params_solved','visibility_periods_used','astrometric_excess_noise','duplicated_source','ipd_frac_multi_peak','ipd_gof_harmonic_amplitude','non_single_star']
 q="SELECT column_name,datatype,description FROM TAP_SCHEMA.columns WHERE table_name='gaiadr3.gaia_source' AND column_name IN ("+','.join("'"+x+"'" for x in wanted)+") ORDER BY column_name"
 txt=tap(q); lines=[x for x in txt.splitlines() if x.strip()]
 found=[]
 for line in lines[1:]: found.append(line.split(',')[0].strip().strip('"'))
 out['wanted']=wanted;out['found']=found;out['missing']=sorted(set(wanted)-set(found));out['raw_schema_csv']=txt[:30000]
 out['success']=len(out['missing'])==0;out['decision']='GAIA_QUALITY_SCHEMA_READY' if out['success'] else 'GAIA_QUALITY_SCHEMA_INCOMPLETE'
except Exception as e:
 out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
