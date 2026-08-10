#!/usr/bin/env python3
"""Run one exact frozen literature comparator on one final SonotaCo year before truth opens."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_comparators_v1 import pretruth_comparators as comp
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_module, require, sha256_path

HDBSCAN_DEPENDENCY_COMMIT="a15737166cc9e1917f2e3d1b63cc42096008ae2e"
HDBSCAN_DEPENDENCY_PATH="orbittrace_literature_comparison/literature_comparators.py"
HDBSCAN_DEPENDENCY_BLOB_SHA="ab17e1205d72d8ab8361d8ba6cdad2e4c31fdcb2"


def dump(path:Path,value:Any)->str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--comparator",choices=["sugar","hdbscan"],required=True); p.add_argument("--year",type=int,choices=[2013,2014],required=True)
    p.add_argument("--rows",type=Path,required=True); p.add_argument("--source",type=Path,required=True); p.add_argument("--output",type=Path,required=True); return p.parse_args()


def materialize_hdbscan_dependency(output:Path)->dict[str,str]:
    """Restore only the runner's exact frozen source dependency from its pinned source commit."""
    subprocess.run(["git","fetch","--no-tags","--depth=1","origin",HDBSCAN_DEPENDENCY_COMMIT],check=True)
    raw=subprocess.check_output(["git","show",f"{HDBSCAN_DEPENDENCY_COMMIT}:{HDBSCAN_DEPENDENCY_PATH}"])
    dep_dir=output/"frozen_hdbscan_dependency"; dep_dir.mkdir(parents=True,exist_ok=True)
    dep_path=dep_dir/"literature_comparators.py"; dep_path.write_bytes(raw)
    blob=subprocess.check_output(["git","hash-object",str(dep_path)],text=True).strip()
    require(blob==HDBSCAN_DEPENDENCY_BLOB_SHA,f"HDBSCAN dependency blob identity changed: {blob}")
    sys.path.insert(0,str(dep_dir.resolve()))
    return {
        "source_commit":HDBSCAN_DEPENDENCY_COMMIT,
        "repository_path":HDBSCAN_DEPENDENCY_PATH,
        "git_blob_sha":blob,
        "sha256":sha256_path(dep_path),
    }


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True); rows=json.loads(a.rows.read_text()); require(isinstance(rows,list) and rows,"empty comparator rows")
    dependency:dict[str,str]|None=None
    if a.comparator=="sugar":
        require(sha256_path(a.source)==comp.SUGAR_CORE_SHA256,"Sugar source identity changed")
        module=load_module(a.source,"final_sugar_core"); module.__source_sha256__=comp.SUGAR_CORE_SHA256
        result=comp.run_sugar(rows,year=a.year,sugar=module)
    else:
        require(sha256_path(a.source)==comp.HDBSCAN_SOURCE_SHA256,"HDBSCAN source identity changed")
        dependency=materialize_hdbscan_dependency(a.output)
        module=load_module(a.source,"final_hdbscan_runner"); module.__source_sha256__=comp.HDBSCAN_SOURCE_SHA256
        result=comp.run_hdbscan(rows,year=a.year,hdbscan_runner=module,core_dist_jobs=1)
    source_manifest={"comparator":result["method"],"year":a.year,"scientific_source_sha256":sha256_path(a.source),"adapter_sha256":sha256_path(Path(comp.__file__)),"hdbscan_frozen_dependency":dependency,"truth_labels_accepted":False,"target_information_access":False}
    source_sha=dump(a.output/"comparator_source_manifest.json",source_manifest)
    result["source_manifest_sha256"]=source_sha
    primary_sha=dump(a.output/"comparator_primary_output.json",result)
    summary={"verdict":"PASS_FINAL_PRETRUTH_COMPARATOR_OUTPUT_FREEZE","comparator":a.comparator,"year":a.year,"primary_output_sha256":primary_sha,"source_manifest_sha256":source_sha,"family_count":result["retained_family_count"],"truth_accessed":False}
    dump(a.output/"comparator_pretruth_summary.json",summary); print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
