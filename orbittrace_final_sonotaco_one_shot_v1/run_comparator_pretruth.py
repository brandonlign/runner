#!/usr/bin/env python3
"""Run one exact frozen literature comparator on one final SonotaCo year before truth opens."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_comparators_v1 import pretruth_comparators as comp
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_module, require, sha256_path


def dump(path:Path,value:Any)->str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--comparator",choices=["sugar","hdbscan"],required=True); p.add_argument("--year",type=int,choices=[2013,2014],required=True)
    p.add_argument("--rows",type=Path,required=True); p.add_argument("--source",type=Path,required=True); p.add_argument("--output",type=Path,required=True); return p.parse_args()


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True); rows=json.loads(a.rows.read_text()); require(isinstance(rows,list) and rows,"empty comparator rows")
    if a.comparator=="sugar":
        require(sha256_path(a.source)==comp.SUGAR_CORE_SHA256,"Sugar source identity changed")
        module=load_module(a.source,"final_sugar_core"); module.__source_sha256__=comp.SUGAR_CORE_SHA256
        result=comp.run_sugar(rows,year=a.year,sugar=module)
    else:
        require(sha256_path(a.source)==comp.HDBSCAN_SOURCE_SHA256,"HDBSCAN source identity changed")
        module=load_module(a.source,"final_hdbscan_runner"); module.__source_sha256__=comp.HDBSCAN_SOURCE_SHA256
        result=comp.run_hdbscan(rows,year=a.year,hdbscan_runner=module,core_dist_jobs=1)
    source_manifest={"comparator":result["method"],"year":a.year,"scientific_source_sha256":sha256_path(a.source),"adapter_sha256":sha256_path(Path(comp.__file__)),"truth_labels_accepted":False,"target_information_access":False}
    source_sha=dump(a.output/"comparator_source_manifest.json",source_manifest)
    result["source_manifest_sha256"]=source_sha
    primary_sha=dump(a.output/"comparator_primary_output.json",result)
    summary={"verdict":"PASS_FINAL_PRETRUTH_COMPARATOR_OUTPUT_FREEZE","comparator":a.comparator,"year":a.year,"primary_output_sha256":primary_sha,"source_manifest_sha256":source_sha,"family_count":result["retained_family_count"],"truth_accessed":False}
    dump(a.output/"comparator_pretruth_summary.json",summary); print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
