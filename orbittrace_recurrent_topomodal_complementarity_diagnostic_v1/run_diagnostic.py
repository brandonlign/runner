#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

YEARS = (2013, 2014)
RECURRENT_SHA = "19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078"
TOPOMODAL_SHA = "f673c2b3ace66e39020a05e077172370a0c026acc0fd40446773089600cba991"
EXPECTED_CG = {2013: 16, 2014: 16}


def req(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recurrent-result", type=Path, required=True)
    ap.add_argument("--topomodal-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(sha256(args.recurrent_result) == RECURRENT_SHA, "recurrent result SHA-256 mismatch")
    req(sha256(args.topomodal_result) == TOPOMODAL_SHA, "TopoModal result SHA-256 mismatch")

    recurrent = load(args.recurrent_result)
    topomodal = load(args.topomodal_result)

    req(recurrent.get("schema") == "ORBITTRACE_RECURRENT_EOM_RESIDUAL_ANALYSIS_V1", "recurrent schema")
    req(recurrent.get("parent_method") == "recurrent-EOM HDBSCAN v1", "recurrent parent method")
    req(recurrent.get("scientific_role") == "EXPOSED_SONOTACO_DEVELOPMENT_DIAGNOSTIC_ONLY", "recurrent role")
    req(recurrent.get("target_information_access") is False, "recurrent target-information firewall")
    req(recurrent.get("target_region_events_accessed") is False, "recurrent target-region firewall")
    req(recurrent.get("pristine_external_access") is False, "recurrent pristine-external firewall")

    req(topomodal.get("schema") == "ORBITTRACE_TOPOMODAL_FULL_RECOVERABILITY_DIAGNOSTIC_V1", "TopoModal schema")
    req(topomodal.get("scientific_role") == "EXPOSED_SONOTACO_DEVELOPMENT_DIAGNOSTIC_ONLY", "TopoModal role")
    req(topomodal.get("protected_target_access") is False, "TopoModal protected-target firewall")
    req(topomodal.get("method_mutation") is False, "TopoModal method-mutation flag")

    rpanels: dict[int, dict[str, Any]] = {}
    for panel in recurrent.get("panels", []):
        if panel.get("route") != "hdbscan":
            continue
        year = int(panel["year"])
        req(year in YEARS, f"unexpected recurrent HDBSCAN-route year {year}")
        req(year not in rpanels, f"duplicate recurrent HDBSCAN-route panel {year}")
        rpanels[year] = panel
    req(set(rpanels) == set(YEARS), "missing recurrent HDBSCAN-route panel")

    tpanels: dict[int, dict[str, Any]] = {}
    for panel in topomodal.get("panels", []):
        year = int(panel["year"])
        req(year in YEARS, f"unexpected TopoModal year {year}")
        req(year not in tpanels, f"duplicate TopoModal panel {year}")
        tpanels[year] = panel
    req(set(tpanels) == set(YEARS), "missing TopoModal panel")

    panel_results: list[dict[str, Any]] = []
    pooled_records: list[dict[str, Any]] = []

    for year in YEARS:
        rpanel = rpanels[year]
        cg = [r for r in rpanel.get("records", []) if r.get("category") == "CANDIDATE_GENERATION_FAILURE"]
        req(len(cg) == EXPECTED_CG[year], f"candidate-generation count changed for {year}")
        req(int(rpanel["category_counts"]["CANDIDATE_GENERATION_FAILURE"]) == EXPECTED_CG[year], f"category-count mismatch {year}")

        per_label = tpanels[year].get("per_label", [])
        topo_by_label: dict[str, dict[str, Any]] = {}
        for row in per_label:
            label = str(row["label"])
            req(label not in topo_by_label, f"duplicate TopoModal label {year} {label}")
            topo_by_label[label] = row

        records: list[dict[str, Any]] = []
        for rec in cg:
            label = str(rec["truth_label"])
            req(label in topo_by_label, f"missing TopoModal label {year} {label}")
            tr = topo_by_label[label]
            best = float(tr["topomodal_best_f1"])
            covered = best > 0.5
            row = {
                "year": year,
                "truth_label": label,
                "recurrent_best_all_f1": float(rec["best_all_f1"]),
                "topomodal_best_f1": best,
                "topomodal_first_rank_f1_gt_0_5": tr.get("topomodal_first_rank_f1_gt_0_5"),
                "classification": "TOPOMODAL_COMPLEMENTARY_RECOVERY" if covered else "NOT_RECOVERED_BY_TOPOMODAL",
            }
            records.append(row)
            pooled_records.append(row)

        records.sort(key=lambda x: x["truth_label"])
        recovered = sum(r["classification"] == "TOPOMODAL_COMPLEMENTARY_RECOVERY" for r in records)
        total = len(records)
        panel_results.append({
            "year": year,
            "recurrent_candidate_generation_failures": total,
            "topomodal_complementary_recoveries": recovered,
            "not_recovered_by_topomodal": total - recovered,
            "complementary_recovery_fraction": recovered / total,
            "records": records,
        })

    pooled_recovered = sum(r["classification"] == "TOPOMODAL_COMPLEMENTARY_RECOVERY" for r in pooled_records)
    pooled_total = len(pooled_records)
    req(pooled_total == 32, "pooled HDBSCAN-route candidate-generation count changed")

    result = {
        "schema": "ORBITTRACE_RECURRENT_TOPOMODAL_COMPLEMENTARITY_DIAGNOSTIC_V1",
        "scientific_role": "POST_OBSERVATION_EXPOSED_SONOTACO_REPRODUCIBILITY_AUDIT_ONLY",
        "blind_preregistration": False,
        "provisional_intersection_observed_before_protocol_commit": True,
        "input_sha256": {
            "recurrent_residual_result": RECURRENT_SHA,
            "topomodal_full_recoverability_result": TOPOMODAL_SHA,
        },
        "criterion": "recurrent category == CANDIDATE_GENERATION_FAILURE and TopoModal topomodal_best_f1 > 0.5",
        "route": "hdbscan",
        "panels": panel_results,
        "pooled": {
            "recurrent_candidate_generation_failures": pooled_total,
            "topomodal_complementary_recoveries": pooled_recovered,
            "not_recovered_by_topomodal": pooled_total - pooled_recovered,
            "complementary_recovery_fraction": pooled_recovered / pooled_total,
        },
        "method_mutation": False,
        "new_clustering_or_candidate_generation": False,
        "raw_truth_reparsed": False,
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "pristine_external_access": False,
        "interpretation_boundary": "Candidate-existence complementarity only; does not establish or authorize budgeted union performance.",
    }

    result_sha = dump(args.output / "COMPLEMENTARITY_RESULT.json", result)
    head = git_head()
    (args.output / "execution_commit.txt").write_text(head + "\n")
    (args.output / "environment.txt").write_text(
        f"python={platform.python_version()}\nplatform={platform.platform()}\n"
    )

    print(json.dumps({
        "result_sha256": result_sha,
        "execution_commit": head,
        "panels": [
            {
                "year": p["year"],
                "recurrent_candidate_generation_failures": p["recurrent_candidate_generation_failures"],
                "topomodal_complementary_recoveries": p["topomodal_complementary_recoveries"],
                "complementary_recovery_fraction": p["complementary_recovery_fraction"],
            }
            for p in panel_results
        ],
        "pooled": result["pooled"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
