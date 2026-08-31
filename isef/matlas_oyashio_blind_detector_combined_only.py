#!/usr/bin/env python3
"""Runtime split of the Oyashio v2 pilot: exact combined F814W DRC only.

No detector parameter or calculation changes. This avoids repeating the heavy
whole-field Hessian scan over sub-association products before the decisive deep
positive-control result is known. No MATLAS Table-A.1 target is queried.
"""
from pathlib import Path
import matlas_oyashio_blind_detector_pilot as p
import matlas_oyashio_blind_detector_pilot_v2 as v2

orig_query=p.query_products

def combined_query():
    rows=orig_query()
    hit=[r for r in rows if r['filename']==p.EXPECTED_COMBINED]
    if len(hit)!=1:raise RuntimeError(f'exact combined product resolution failed: {hit}')
    return hit

if __name__=='__main__':
    p.OUT=Path('results/matlas_oyashio_blind_detector_combined_only');p.OUT.mkdir(parents=True,exist_ok=True)
    p.DOWNLOAD=p.OUT/'download';p.DOWNLOAD.mkdir(exist_ok=True)
    p.query_products=combined_query
    p.detect=v2.detect_v2
    p.main()
