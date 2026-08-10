#!/usr/bin/env python3
"""Open final SonotaCo truth only after all pretruth hashes are frozen, then call exact #854."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_module, require, sha256_path

EVALUATOR_SHA="cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c"
PAIRS=(("sugar","Sugar"),("hdbscan","catalogue HDBSCAN"))
YEARS=(2013,2014)


def load(path:Path)->Any: return json.loads(path.read_text())
def dump(path:Path,value:Any)->str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); path.write_bytes(raw); return hashlib.sha256(raw).hexdigest()
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--csv-2013",type=Path,required=True); p.add_argument("--csv-2014",type=Path,required=True); p.add_argument("--mapping-audit",type=Path,required=True); p.add_argument("--evaluator-source",type=Path,required=True)
    p.add_argument("--prepare-dir",type=Path,required=True); p.add_argument("--freeze-dir",type=Path,required=True); p.add_argument("--candidate-sugar-dir",type=Path,required=True); p.add_argument("--candidate-hdbscan-dir",type=Path,required=True)
    p.add_argument("--comparator-sugar-2013-dir",type=Path,required=True); p.add_argument("--comparator-sugar-2014-dir",type=Path,required=True); p.add_argument("--comparator-hdbscan-2013-dir",type=Path,required=True); p.add_argument("--comparator-hdbscan-2014-dir",type=Path,required=True)
    p.add_argument("--source-integrity",type=Path,required=True); p.add_argument("--output",type=Path,required=True); return p.parse_args()


def evaluator_families_candidate(payload:dict[str,Any])->list[dict[str,Any]]:
    return [{"family_id":str(f["family_id"]),"event_ids":[str(x) for x in f["event_ids"]]} for f in payload["families"]]

def evaluator_families_comparator(payload:dict[str,Any])->list[dict[str,Any]]:
    return [{"family_id":str(f["family_id"]),"event_ids":[str(x) for x in f["member_ids"]]} for f in payload["families"]]


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    integrity=load(a.source_integrity); require(integrity.get("authorization_state")=="AUTHORIZED_FINAL_SONOTACO_2013_2014_EXECUTION","authorization lost")
    require(integrity.get("target_access_authorized") is False and integrity.get("maarsy_access_authorized") is False,"forbidden downstream authorization")
    require(sha256_path(a.mapping_audit)==truth_reader.MAPPING_AUDIT_SHA256,"mapping audit identity changed")
    require(sha256_path(a.evaluator_source)==EVALUATOR_SHA,"final evaluator source identity changed")
    evaluator=load_module(a.evaluator_source,"final_matched_evaluator")
    mapping=load(a.mapping_audit); csvs={2013:a.csv_2013.read_bytes(),2014:a.csv_2014.read_bytes()}
    cand_dirs={"sugar":a.candidate_sugar_dir,"hdbscan":a.candidate_hdbscan_dir}
    comp_dirs={("sugar",2013):a.comparator_sugar_2013_dir,("sugar",2014):a.comparator_sugar_2014_dir,("hdbscan",2013):a.comparator_hdbscan_2013_dir,("hdbscan",2014):a.comparator_hdbscan_2014_dir}
    evaluations:dict[str,list[dict[str,Any]]]={"sugar":[],"hdbscan":[]}; truth_audits:dict[str,Any]={}
    for key,display in PAIRS:
        candidate_path=cand_dirs[key]/"candidate_primary_output.json"; candidate=load(candidate_path); candidate_families=evaluator_families_candidate(candidate)
        truth_audits[key]={}
        for year in YEARS:
            rows_path=a.prepare_dir/f"{key}_{year}.json"; rows=load(rows_path); row_ids=[str(x["id"]) for x in rows]
            comp_path=comp_dirs[(key,year)]/"comparator_primary_output.json"; comp_payload=load(comp_path); comp_families=evaluator_families_comparator(comp_payload)
            freeze_path=a.freeze_dir/f"pretruth_freeze_{key}_{year}.json"; freeze=load(freeze_path)
            require(freeze["pairwise_rows_json_sha256"]==sha(rows_path),"pairwise rows changed after freeze")
            require(freeze["orbittrace_primary_output_sha256"]==sha(candidate_path),"candidate output changed after freeze")
            require(freeze["comparator_primary_output_sha256"]==sha(comp_path),"comparator output changed after freeze")
            require(freeze["orbittrace_source_manifest_sha256"]==sha(cand_dirs[key]/"candidate_source_manifest.json"),"candidate source manifest changed after freeze")
            require(freeze["comparator_source_manifest_sha256"]==sha(comp_dirs[(key,year)]/"comparator_source_manifest.json"),"comparator source manifest changed after freeze")
            truth,audit=truth_reader.parse_truth_after_freeze(
                csvs[year],year=year,comparator=display,requested_event_ids=row_ids,mapping_audit=mapping,
                mapping_audit_sha256=truth_reader.MAPPING_AUDIT_SHA256,pretruth_freeze=freeze,id_prefix=f"SNT{year}",
            )
            truth_sha=dump(a.output/f"truth_{key}_{year}.json",truth); audit["truth_sha256"]=truth_sha; dump(a.output/f"truth_audit_{key}_{year}.json",audit); truth_audits[key][str(year)]=audit
            evaluation=evaluator.evaluate_pair(candidate_families,comp_families,truth,row_ids,year,display)
            evaluations[key].append(evaluation); dump(a.output/f"evaluation_{key}_{year}.json",evaluation)
    final=evaluator.final_verdict(evaluations["sugar"],evaluations["hdbscan"])
    result={
        "scientific_stage":"FINAL_MATCHED_LITERATURE_TEST_SONOTACO_2013_2014",
        "final_candidate":"M0/#839","years":[2013,2014],"comparators":["Sugar","catalogue HDBSCAN"],
        "verdict":final["verdict"],"final_evaluator":final,"pair_evaluations":evaluations,"truth_audits":truth_audits,
        "evaluator_source_sha256":EVALUATOR_SHA,"mapping_audit_sha256":truth_reader.MAPPING_AUDIT_SHA256,
        "posttruth_method_mutation":False,"maarsy_scientific_access":False,"target_information_access":False,
    }
    result_sha=dump(a.output/"FINAL_LITERATURE_RESULT_V1.json",result)
    print(json.dumps({"verdict":result["verdict"],"result_sha256":result_sha,"maarsy_scientific_access":False,"target_information_access":False},indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
