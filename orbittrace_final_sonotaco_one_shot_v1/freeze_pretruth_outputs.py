#!/usr/bin/env python3
"""Freeze exact row/output/source hashes before final SonotaCo truth is allowed to open."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_truth_v1.truth_boundary import canonical_ids_sha256

PAIRS=(("sugar","Sugar"),("hdbscan","catalogue HDBSCAN"))
YEARS=(2013,2014)


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path:Path)->Any: return json.loads(path.read_text())
def dump(path:Path,value:Any)->str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--prepare-dir",type=Path,required=True); p.add_argument("--candidate-sugar-dir",type=Path,required=True); p.add_argument("--candidate-hdbscan-dir",type=Path,required=True)
    p.add_argument("--comparator-sugar-2013-dir",type=Path,required=True); p.add_argument("--comparator-sugar-2014-dir",type=Path,required=True); p.add_argument("--comparator-hdbscan-2013-dir",type=Path,required=True); p.add_argument("--comparator-hdbscan-2014-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True); return p.parse_args()


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    cand_dirs={"sugar":a.candidate_sugar_dir,"hdbscan":a.candidate_hdbscan_dir}
    comp_dirs={("sugar",2013):a.comparator_sugar_2013_dir,("sugar",2014):a.comparator_sugar_2014_dir,("hdbscan",2013):a.comparator_hdbscan_2013_dir,("hdbscan",2014):a.comparator_hdbscan_2014_dir}
    freeze_index={"verdict":"PASS_FINAL_PRETRUTH_HASH_FREEZE","panels":{},"truth_accessed":False,"target_information_access":False}
    for key,display in PAIRS:
        candidate_primary=cand_dirs[key]/"candidate_primary_output.json"; candidate_source=cand_dirs[key]/"candidate_source_manifest.json"
        require(candidate_primary.is_file() and candidate_source.is_file(),f"missing {key} candidate output")
        candidate=load(candidate_primary); require(candidate.get("truth_accessed") is False,"candidate truth flag violated")
        freeze_index["panels"][key]={}
        for year in YEARS:
            rows_file=a.prepare_dir/f"{key}_{year}.json"; rows=load(rows_file); ids=[str(x["id"]) for x in rows]
            comparator_primary=comp_dirs[(key,year)]/"comparator_primary_output.json"; comparator_source=comp_dirs[(key,year)]/"comparator_source_manifest.json"
            require(comparator_primary.is_file() and comparator_source.is_file(),f"missing {key}/{year} comparator output")
            comp=load(comparator_primary); require(comp.get("truth_accessed") is False,"comparator truth flag violated")
            manifest={
                "year":year,"comparator":display,"pretruth_outputs_frozen":True,"truth_accessed_before_freeze":False,
                "target_information_access":False,"target_region_access":False,
                "pairwise_event_ids_sha256":canonical_ids_sha256(ids),
                "orbittrace_primary_output_sha256":sha(candidate_primary),
                "comparator_primary_output_sha256":sha(comparator_primary),
                "orbittrace_source_manifest_sha256":sha(candidate_source),
                "comparator_source_manifest_sha256":sha(comparator_source),
                "pairwise_rows_json_sha256":sha(rows_file),
            }
            out=a.output/f"pretruth_freeze_{key}_{year}.json"; freeze_sha=dump(out,manifest)
            freeze_index["panels"][key][str(year)]={"freeze_manifest_sha256":freeze_sha,"event_count":len(ids),"event_ids_sha256":manifest["pairwise_event_ids_sha256"]}
    index_sha=dump(a.output/"pretruth_freeze_index.json",freeze_index)
    print(json.dumps({"verdict":freeze_index["verdict"],"index_sha256":index_sha,"truth_accessed":False},indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
