#!/usr/bin/env python3
"""Run frozen M0/#839 on one comparator-specific SonotaCo 2013/2014 row pair before truth opens."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_urc_pair_portable_generators_v1 import generators
from orbittrace_urc_unseen_ranker_v1 import application
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_module, load_support_base, require, sha256_path

YEARS=(2013,2014)
MODEL_SHA="ac48355e8c51de2a9cfa12f23b2a847f5e946fc03336a941f80d98224ee5c909"
RANKER_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
GENERATOR_SOURCE_COMMIT="7dd59b5d2be7c0040f42ee494c9bd8b71ccb0d8b"
GENERATOR_EQ_RUN=31348847806
GENERATOR_EQ_ARTIFACT=9048521513
GENERATOR_EQ_DIGEST="sha256:4bfb87af3b6c09afdcc62226022d68a995139eda64031fb57169f9a99c510751"


def dump(path:Path,value:Any)->str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode(); path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--comparator",choices=["sugar","hdbscan"],required=True)
    p.add_argument("--rows-2013",type=Path,required=True); p.add_argument("--rows-2014",type=Path,required=True)
    p.add_argument("--v8-source",type=Path,required=True); p.add_argument("--p19-source",type=Path,required=True); p.add_argument("--p20-source",type=Path,required=True)
    p.add_argument("--active-ranker-source",type=Path,required=True); p.add_argument("--model-joblib",type=Path,required=True)
    p.add_argument("--support-source-parts",type=Path,required=True); p.add_argument("--candidate-payload",type=Path,required=True); p.add_argument("--baseline-payload",type=Path,required=True); p.add_argument("--scorer-parts",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    return p.parse_args()


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha256_path(a.model_joblib)==MODEL_SHA,"serialized ranker identity changed")
    require(sha256_path(a.active_ranker_source)==RANKER_SHA,"active frozen ranker source changed")
    scan={2013:json.loads(a.rows_2013.read_text()),2014:json.loads(a.rows_2014.read_text())}
    for year in YEARS:
        require(scan[year] and all(int(x.get("year"))==year for x in scan[year]),f"invalid {year} row universe")
        forbidden={"label","shower","truth","known_shower","native_background","sporadic"}
        require(all(not (forbidden & set(x)) for x in scan[year]),"truth-bearing field in candidate input")

    v8=load_module(a.v8_source,"final_sonotaco_v8")
    p19=load_module(a.p19_source,"final_sonotaco_p19")
    p20=load_module(a.p20_source,"final_sonotaco_p20")
    urc=load_module(a.active_ranker_source,"final_sonotaco_urc_ranker")
    runtime,support,base,_scorer=load_support_base(
        p19_module=p19,support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,
    )
    mult=p19.mult; v6=p19.v6
    require(p20.mult is not None,"P20 multiplicity runtime unavailable")
    generators.configure_pair(YEARS,support=support,mult=mult,v6=v6,v8=v8,p19=p19,p20=p20)
    built=generators.build_union_pair(
        years=YEARS,scan_by_year=scan,support=support,base=base,runtime=runtime,v6=v6,v8=v8,p19=p19,p20=p20,mult=mult,
    )
    hard=list(built["hard"]["hard_families"]); p19_soft=list(built["p19_soft"]); p20_soft=list(built["p20"]["soft_families"])
    families=hard+p19_soft+p20_soft
    require(families,"#839 produced no candidate families")
    source_by_id={str(f["family_id"]):"hard" for f in hard}
    source_by_id.update({str(f["family_id"]):"p19" for f in p19_soft})
    source_by_id.update({str(f["family_id"]):"p20" for f in p20_soft})
    hard_order=[str(x) for x in built["hard_order"]]
    rank=application.score_and_rank(
        model_path=a.model_joblib,families=families,source_by_id=source_by_id,hard_order=hard_order,
        scan_by_year=scan,years=YEARS,support=support,base=base,frozen_ranker_module=urc,
    )
    by_id={str(f["family_id"]):f for f in families}
    ordered=[]
    for position,fid in enumerate(rank["order"],start=1):
        family=by_id[str(fid)]
        ids=[str(x) for x in family["event_ids"]]
        require(ids and len(ids)==len(set(ids)),f"invalid family members: {fid}")
        ordered.append({"family_id":str(fid),"event_ids":ids,"rank":position,"source":source_by_id[str(fid)]})
    X=np.asarray(rank["feature_matrix"],dtype=np.float64); pred=np.asarray(rank["prediction"],dtype=np.float64)
    source_manifest={
        "method":"M0/#839","comparator_pair":a.comparator,"generator_equivalence_source_commit":GENERATOR_SOURCE_COMMIT,
        "generator_equivalence_run_id":GENERATOR_EQ_RUN,"generator_equivalence_artifact_id":GENERATOR_EQ_ARTIFACT,
        "generator_equivalence_artifact_digest":GENERATOR_EQ_DIGEST,"model_sha256":MODEL_SHA,"active_ranker_source_sha256":RANKER_SHA,
        "generator_adapter_sha256":sha256_path(Path(generators.__file__)),"ranker_application_sha256":sha256_path(Path(application.__file__)),
        "v8_source_sha256":sha256_path(a.v8_source),"p19_source_sha256":sha256_path(a.p19_source),"p20_source_sha256":sha256_path(a.p20_source),
        "truth_labels_accepted":False,"target_information_access":False,
    }
    source_sha=dump(a.output/"candidate_source_manifest.json",source_manifest)
    primary={
        "method":"M0/#839","comparator_pair":a.comparator,"years":[2013,2014],
        "input_counts":{str(y):len(scan[y]) for y in YEARS},
        "candidate_counts":{"hard":len(hard),"p19_soft":len(p19_soft),"p20_soft":len(p20_soft),"union":len(families)},
        "feature_matrix_sha256":application.array_sha256(X),"prediction_sha256":application.array_sha256(pred),
        "application_order_sha256":rank["order_sha256"],"family_count":len(ordered),"families":ordered,
        "source_manifest_sha256":source_sha,"truth_accessed":False,"target_information_access":False,
    }
    primary_sha=dump(a.output/"candidate_primary_output.json",primary)
    summary={"verdict":"PASS_FINAL_PRETRUTH_URC_OUTPUT_FREEZE","comparator_pair":a.comparator,"primary_output_sha256":primary_sha,"source_manifest_sha256":source_sha,"family_count":len(ordered),"truth_accessed":False}
    dump(a.output/"candidate_pretruth_summary.json",summary)
    print(json.dumps(summary,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
