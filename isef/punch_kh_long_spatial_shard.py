#!/usr/bin/env python3
"""Exact file-shard executor for the frozen long/radial spatial gate.

TARGET BLIND. This does not define a new scientific analysis: it imports and
calls punch_kh_long_oriented_spatial_gate.trial unchanged. The only change is
scheduling one of the three already-frozen CTM files per Actions job so the
three independent file blocks can run concurrently.
"""
from __future__ import annotations
import json,os
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from astropy.io import fits

import punch_kh_real_background_controls_v2 as bg
import punch_kh_long_oriented_spatial_gate as ls


def main():
    fi=int(os.environ['PUNCH_SPATIAL_FILE_INDEX'])
    selected=bg.choose_files()
    if fi<0 or fi>=len(selected):raise RuntimeError(f'bad file shard {fi}')
    _,name=selected[fi]
    out=Path(f'results/punch_kh_long_spatial_shard_{fi}');out.mkdir(parents=True,exist_ok=True)
    path=bg.download(name);tasks=[]
    try:
        with fits.open(path,memmap=True) as h:
            data=h[1].data
            for label,field in ls.FIELDS.items():
                strip=ls.radial_source_strip(data,field);z,stats=bg.standardize(strip)
                if z is None:raise RuntimeError(f'invalid {label}: {stats}')
                for w in ls.WAVES:tasks.append((name,label,z,w,'growth',0))
                tasks.append((name,label,z,40.,'step',0))
                tasks.append((name,label,z,40.,'random_knots',5000+fi))
        trials=[]
        with ProcessPoolExecutor(max_workers=4) as pool:
            fut=[pool.submit(ls.trial,t) for t in tasks]
            for n,f in enumerate(as_completed(fut),1):
                trials.append(f.result())
                if n%4==0:
                    # Durable progress inside the workspace; artifact is uploaded
                    # at job end. Scientific result is still the complete shard.
                    (out/'progress.json').write_text(json.dumps({'file_index':fi,'file':name,'completed':n,'total':len(tasks)},indent=2)+'\n')
                    print('SHARD',fi,'completed',n,'/',len(tasks),flush=True)
        if len(trials)!=48:raise RuntimeError(f'shard {fi} expected 48 trials, got {len(trials)}')
        report={'information_barrier':'one frozen 2025-09-21 non-R3 CTM file only; zero R3 pixels','file_index':fi,'file':name,'exact_trial_implementation':'punch_kh_long_oriented_spatial_gate.trial','trials':trials}
        (out/'shard.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'file_index':fi,'file':name,'n_trials':len(trials)},indent=2))
        return 0
    finally:
        try:path.unlink()
        except OSError:pass

if __name__=='__main__':raise SystemExit(main())
