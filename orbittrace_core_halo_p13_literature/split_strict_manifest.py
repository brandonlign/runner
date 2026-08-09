#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PANELS=('hdbscan','sugar')
YEARS=(2023,2025)
EXPECTED_COUNTS={'hdbscan':{2023:26460,2025:19658},'sugar':{2023:30414,2025:23200}}
EXPECTED_HASHES={
    'hdbscan_2023':'35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',
    'hdbscan_2025':'8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3',
    'sugar_2023':'2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',
    'sugar_2025':'77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e',
}


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--output-dir',required=True,type=Path); a=p.parse_args()
    m=json.loads(a.input.read_text())
    require(m['classification']=='P2 matched-literature strict pretruth ID-only manifest','wrong combined strict manifest')
    require(m['years']==list(YEARS) and m['blind_exclusion']==[20.0,55.0],'strict manifest universe changed')
    require(m['competitor_cluster_values_parsed'] is False,'competitor values entered strict manifest')
    require(m['known_shower_truth_values_parsed'] is False,'truth values entered strict manifest')
    require(m['native_shower_tokens_parsed'] is False,'native shower tokens entered strict manifest')
    side=a.input.with_suffix(a.input.suffix+'.sha256'); require(side.exists() and side.read_text().strip()==canonical_sha(m),'combined strict manifest hash mismatch')
    require(m['input_hashes']==EXPECTED_HASHES,'assignment source hashes changed')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for panel in PANELS:
        for year in YEARS:
            block=m['panels'][panel][str(year)]
            ids=list(map(str,block['scan_ids']))
            require(block['scan_count']==EXPECTED_COUNTS[panel][year] and len(ids)==EXPECTED_COUNTS[panel][year],f'{panel} {year} count changed')
            require(len(ids)==len(set(ids)) and all(x.startswith(f'SNM{year}:') for x in ids),f'{panel} {year} ID universe invalid')
            out={
                'classification':'P13 matched-literature strict panel-year ID-only manifest',
                'panel':panel,
                'year':year,
                'blind_exclusion':[20.0,55.0],
                'event_ids':ids,
                'event_count':len(ids),
                'assignment_source_sha256':EXPECTED_HASHES[f'{panel}_{year}'],
                'competitor_cluster_values_accessed':False,
                'known_shower_truth_accessed':False,
                'source_combined_manifest_sha256':canonical_sha(m),
            }
            path=a.output_dir/f'{panel}_{year}.json'; path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); path.with_suffix(path.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('PASS_P13_STRICT_MANIFEST_SPLIT_ID_ONLY_NO_VALUES')
    return 0


if __name__=='__main__': raise SystemExit(main())
