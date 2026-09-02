#!/usr/bin/env python3
from pathlib import Path
import json
from astroquery.esa.xmm_newton import XMMNewton
OUT=Path('results/xsa_stack_schema_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
try:
    tabs=[str(x) for x in XMMNewton.get_tables(only_names=True)]
    matches=[t for t in tabs if ('stack' in t.lower() or 'epic' in t.lower() or 'xmm' in t.lower())]
    probes=[]
    for target in matches:
        try:
            cnt=XMMNewton.query_xsa_tap(f'SELECT COUNT(*) AS n FROM {target}')
            probes.append({'table':target,'row_count':int(cnt[0][0])})
        except Exception as e:
            probes.append({'table':target,'error':f'{type(e).__name__}: {e}'})
    out={'success':True,'matching_tables':matches,'probes':probes,'all_table_count':len(tabs)}
except Exception as e:
    out={'success':False,'error':f'{type(e).__name__}: {e}'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
