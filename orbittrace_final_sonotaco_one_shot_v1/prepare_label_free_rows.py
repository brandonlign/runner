#!/usr/bin/env python3
"""Prepare frozen label-free SonotaCo 2013/2014 pairwise row universes.

This stage may run only after final-test authorization. It never reads the `shower` field; the
shared normalizer enforces the 20°–55° firewall before decoding any other scientific field.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from orbittrace_final_sonotaco_normalizer_v1 import normalizer
from orbittrace_final_sonotaco_truth_v1.truth_boundary import canonical_ids_sha256
from orbittrace_final_sonotaco_one_shot_v1.runtime_helpers import load_module, load_support_base, require, sha256_path

YEARS = (2013, 2014)


def dump_json(path: Path, value: Any) -> str:
    raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--csv-2013",type=Path,required=True)
    p.add_argument("--csv-2014",type=Path,required=True)
    p.add_argument("--p19-source",type=Path,required=True)
    p.add_argument("--support-source-parts",type=Path,required=True)
    p.add_argument("--candidate-payload",type=Path,required=True)
    p.add_argument("--baseline-payload",type=Path,required=True)
    p.add_argument("--scorer-parts",type=Path,required=True)
    p.add_argument("--source-integrity",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    return p.parse_args()


def main() -> int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    integrity=json.loads(a.source_integrity.read_text())
    require(integrity.get("authorization_state")=="AUTHORIZED_FINAL_SONOTACO_2013_2014_EXECUTION","final-test authorization missing")
    require(integrity.get("target_access_authorized") is False,"target access must remain false")
    require(integrity.get("maarsy_access_authorized") is False,"MAARSY access must remain false")

    p19=load_module(a.p19_source,"final_prepare_p19")
    _runtime,support,base,_scorer=load_support_base(
        p19_module=p19,support_source_parts=a.support_source_parts,candidate_payload=a.candidate_payload,
        baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts,
    )
    support.CORPUS="orbittrace-final-sonotaco-label-free-prepare-v1"

    csvs={2013:a.csv_2013,2014:a.csv_2014}
    base_rows: dict[int,list[dict[str,Any]]]={}
    audits: dict[int,dict[str,Any]]={}
    for year in YEARS:
        rows,audit=normalizer.normalize_annual_csv(csvs[year].read_bytes(),year=year,base=base,id_prefix=f"SNT{year}")
        require(all(not (normalizer.BLIND_LOW <= float(x["sol"]) <= normalizer.BLIND_HIGH) for x in rows),"target interval survived normalizer")
        require(audit.get("shower_column_row_accessed") is False,"normalizer accessed shower truth")
        require(audit.get("target_region_non_solar_fields_decoded") is False,"target-region science field decoded")
        base_rows[year]=rows; audits[year]=audit
        dump_json(a.output/f"base_{year}.json",rows)
        dump_json(a.output/f"base_audit_{year}.json",audit)

    predicates={"sugar":normalizer.sugar_pairwise_eligible,"hdbscan":normalizer.hdbscan_pairwise_eligible}
    pair_manifest: dict[str,Any]={}
    for key,predicate in predicates.items():
        pair_manifest[key]={}
        for year in YEARS:
            rows=[x for x in base_rows[year] if predicate(x)]
            require(rows,"empty pairwise row universe")
            ids=[str(x["id"]) for x in rows]
            out=a.output/f"{key}_{year}.json"
            file_sha=dump_json(out,rows)
            pair_manifest[key][str(year)]={
                "event_count":len(rows),
                "event_ids_sha256":canonical_ids_sha256(ids),
                "rows_json_sha256":file_sha,
            }

    manifest={
        "verdict":"PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION",
        "years":list(YEARS),
        "base_counts":{str(y):len(base_rows[y]) for y in YEARS},
        "pairwise":pair_manifest,
        "source_integrity":integrity,
        "normalizer_sha256":sha256_path(Path(normalizer.__file__)),
        "shower_truth_accessed":False,
        "target_information_access":False,
        "target_region_retained":False,
        "maarsy_scientific_access":False,
    }
    dump_json(a.output/"label_free_preparation_manifest.json",manifest)
    print(json.dumps(manifest,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
