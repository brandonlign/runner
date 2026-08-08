from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_label_free_all_event_null import run_development as lf


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--year-2022",required=True,type=Path)
    p.add_argument("--year-2023",required=True,type=Path)
    p.add_argument("--repaired-v6-source",required=True,type=Path)
    p.add_argument("--base-runner",required=True,type=Path)
    p.add_argument("--support-source-parts",required=True,type=Path)
    p.add_argument("--candidate-payload",required=True,type=Path)
    p.add_argument("--baseline-payload",required=True,type=Path)
    p.add_argument("--scorer-parts",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()


def load_checkpoint(path:Path,year:int)->dict[str,Any]:
    raw=path.read_bytes(); side=path.with_suffix(".sha256")
    lf.require(side.exists(),f"missing year SHA sidecar {year}")
    lf.require(hashlib.sha256(raw).hexdigest()==side.read_text().strip().split()[0],f"year SHA mismatch {year}")
    c=pickle.loads(raw)
    lf.require(c["format"]=="orbittrace-v6-lf-year-checkpoint-v1" and int(c["year"])==year,f"year checkpoint identity mismatch {year}")
    lf.require(c["repaired_v6_sha256"]==lf.REPAIRED_V6_SHA256,f"repaired source mismatch {year}")
    lf.require(c["firewall"]["label_values_not_accessed"] is True and c["firewall"]["all_event_calibration"] is True,f"year firewall mismatch {year}")
    lf.require(c["firewall"]["scientific_result_not_evaluated"] is True,f"premature evaluation in year {year}")
    return c


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    lf.require(lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256,"repaired v6 identity changed")
    checkpoints={2022:load_checkpoint(args.year_2022,2022),2023:load_checkpoint(args.year_2023,2023)}
    v6=lf.load_module(args.repaired_v6_source,"orbittrace_v6_lf_combine")
    old=v6.load_base_runner(args.base_runner); support=old.load_support_module(args.support_source_parts); _candidate,base,_scorer=support.load_sources(args)
    lf.require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,"blind interval changed")

    scan,calibration,geometry_audits,pretruth_ids=lf.parse_geometry_only(support,base)
    for year in lf.YEARS:
        c=checkpoints[year]
        lf.require(lf.canonical_sha(scan[year])==c["scan_rows_sha256"],f"scan hash mismatch at combine {year}")
        lf.require(lf.canonical_sha(calibration[year])==c["calibration_rows_sha256"],f"calibration hash mismatch at combine {year}")
        rows=[a for a in geometry_audits if str(a["key"]).startswith(str(year))]
        audit_sha=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        lf.require(audit_sha==c["geometry_audit_sha256"],f"geometry audit mismatch at combine {year}")

    components=[]; anchors=[]; year_audits=[]
    for year in lf.YEARS:
        components.extend(checkpoints[year]["components"]); anchors.extend(checkpoints[year]["anchors"]); year_audits.append(checkpoints[year]["audit"])
    primary=v6.build_family_track_v6(old,components,base,"v3")
    rescue=v6.build_family_track_v6(old,components,base,"fixed4_rescue")
    frozen=lf.freeze_families(primary,rescue); pretruth_sha=lf.canonical_sha(frozen)
    frozen_raw=json.dumps(frozen,sort_keys=True,separators=(",",":")).encode()
    (args.output/"v6_lf_pretruth_families.json.gz").write_bytes(__import__('gzip').compress(frozen_raw))
    (args.output/"v6_lf_pretruth.sha256").write_text(pretruth_sha+"\n")

    # FIRST shower-label value access in the fanout execution occurs here.
    hidden_labels,truth_audits=lf.parse_truth_after_freeze(support,pretruth_ids)
    evaluation=v6.evaluate_families_v6(hidden_labels,primary,rescue,lf.YEARS)
    gates={
        "exact_repaired_v6_source":lf.sha256_path(args.repaired_v6_source)==lf.REPAIRED_V6_SHA256,
        "blind_interval_exact":[float(support.BLIND_LOW),float(support.BLIND_HIGH)]==[20.0,55.0],
        "geometry_parser_never_accessed_label_values":all(a["label_value_accessed"] is False for a in geometry_audits),
        "all_event_calibration_exact":all(len(calibration[y])==len(scan[y]) and [e["id"] for e in calibration[y]]==[e["id"] for e in scan[y]] for y in lf.YEARS),
        "at_least_30_supported_bins_each_year":all(len(a["supported_bins"])>=30 for a in year_audits),
        "proposal_budget_exact":all(a["proposal_cap_per_window"]==512 and a["max_primary_proposals_per_year"]==36864 for a in year_audits),
        "pretruth_family_payload_frozen_before_truth":len(pretruth_sha)==64,
        "truth_event_universe_exact":set(hidden_labels)==pretruth_ids,
        "at_least_50_v3_families":int(evaluation["v3_family_count"])>=lf.MIN_FAMILIES,
        "qualified_at_least_v8":int(evaluation["qualified_matches"])>=lf.V8_QUALIFIED,
        "recovery100_at_least_v8":int(evaluation["recovered_at_100"])>=lf.V8_RECOVERY100,
        "mrr_at_least_v8":float(evaluation["mrr"])>=lf.V8_MRR,
        "top100_precision_at_least_065":float(evaluation["top100_dominant_precision"])>=lf.MIN_TOP100_PRECISION,
        "macro_f1_at_least_v8":float(evaluation["macro_f1"])>=lf.V8_MACRO_F1,
    }
    verdict="PASS_V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT" if all(gates.values()) else "FAIL_V6_LABEL_FREE_ALL_EVENT_NULL_NO_GO"
    result={"verdict":verdict,"method":"v6-LF all-event Mondrian null","configuration":{"years":list(lf.YEARS),"blind_exclusion":[20.0,55.0],"calibration_reservoir":"all geometrically valid target-excluded scan events; no shower-label selection","calibration_per_bin":int(old.CALIBRATION_PER_BIN),"proposal_cap_per_window":512,"max_primary_proposals_per_year":36864,"exact_fanout":True,"exact_shards_per_year":int(checkpoints[2022]["execution"]["exact_shard_count"]),"parameter_search":False,"null_trimming":False},"pretruth_sha256":pretruth_sha,"scan_counts":{str(y):len(scan[y]) for y in lf.YEARS},"calibration_counts":{str(y):len(calibration[y]) for y in lf.YEARS},"geometry_audits":geometry_audits,"truth_audits":truth_audits,"year_audits":year_audits,"anchor_count":len(anchors),"component_count":len(components),"family_count":len(primary)+len(rescue),"evaluation":evaluation,"gates":gates,"claim_boundary":"Fully label-free target-excluded development only; no literature-superiority or OrbitTrace recovery claim."}
    (args.output/"v6_label_free_all_event_null_development.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# OrbitTrace v6-LF all-event null fanout development","",f"Verdict: **`{verdict}`**","",f"- primary families: **{evaluation['v3_family_count']}**",f"- qualified: **{evaluation['qualified_matches']}**",f"- recovery@100: **{evaluation['recovered_at_100']}**",f"- MRR: **{evaluation['mrr']:.6f}**",f"- macro F1: **{evaluation['macro_f1']:.6f}**",f"- top-100 precision: **{evaluation['top100_dominant_precision']:.6f}**",f"- pretruth SHA-256: `{pretruth_sha}`","","All shower-label values remained unread until after the combined family payload was durably hash-frozen."]
    (args.output/"V6_LABEL_FREE_ALL_EVENT_NULL_DEVELOPMENT.md").write_text("\n".join(lines)+"\n"); print("\n".join(lines),flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
