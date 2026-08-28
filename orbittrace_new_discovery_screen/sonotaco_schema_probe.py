#!/usr/bin/env python3
"""Print metadata/header structure of one SonotaCo archive; no science output."""
from __future__ import annotations
import io, zipfile, requests, pandas as pd

URL='https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip'
r=requests.get(URL,timeout=240); r.raise_for_status()
with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    print('members=', z.namelist())
    for name in z.namelist():
        if not name.lower().endswith('.csv') or name.startswith('__MACOSX/'):
            continue
        raw=z.read(name)
        print('\nFILE',name,'bytes',len(raw))
        print('first_bytes=',raw[:500].decode('utf-8',errors='replace'))
        for sep in [',',';','\t']:
            try:
                df=pd.read_csv(io.BytesIO(raw),sep=sep,nrows=2,low_memory=False)
                print('sep',repr(sep),'columns=',list(df.columns)[:80])
            except Exception as exc:
                print('sep',repr(sep),'error',type(exc).__name__,str(exc)[:200])
