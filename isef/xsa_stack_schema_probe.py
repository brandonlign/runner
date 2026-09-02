#!/usr/bin/env python3
from pathlib import Path
import json
from astroquery.esa.xmm_newton import XMMNewton
OUT=Path('results/xsa_stack_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
try:
    tabs=XMMNewton.get_tables(only_names=True)
    target='xsa.v_epic_xmm_stack_cat'
    cols=XMMNewton.get_columns(target,only_names=False)
    # Probe row count and a small sample without source identities in output.
    cnt=XMMNewton.query_xsa_tap(f'SELECT COUNT(*) AS n FROM {target}')
    sample=XMMNewton.query_xsa_tap(f'SELECT TOP 1 * FROM {target}')
    out={'success':True,'target_present':target in tabs,'row_count':int(cnt[0][0]),'columns':[str(x.name) for x in cols], 'sample_column_names':list(sample.colnames)}
except Exception as e:
    out={'success':False,'error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
