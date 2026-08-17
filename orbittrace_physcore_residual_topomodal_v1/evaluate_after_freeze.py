#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader

YEARS = (2013, 2014)
PAIRS = ("sugar", "dsh")
DISPLAY = {"sugar": "Sugar", "dsh": "Rudawska-Jenniskens D_SH single linkage"}
MAP_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
EVALUATOR_SHA256 = "cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c"
MATCHED_FREEZE_SHA256 = "690056f48569e1b5049974d970ce736f5af7fc90b2331edb2d72c480979c3be3"
EXPECTED_BUDGETS = {("sugar", 2013): 34, ("sugar", 2014): 46, ("dsh", 2013): 41, ("dsh", 2014): 47}
INHERITED = {
    2013: {"successor_macro_f1": 0.1756351130, "published_hdbscan_macro_f1": 0.1681717489, "successor_recovered": 10, "published_hdbscan_recovered": 10},
    2014: {"successor_macro_f1": 0.1688317479, "published_hdbscan_macro_f1": 0.1568959558, "successor_recovered": 9, "published_hdbscan_recovered": 9},
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def successor_families(payload: dict[str, Any], budget: int) -> list[dict[str, Any]]:
    fams = payload["families"]
    req(len(fams) == int(payload["successor_family_count"]), "successor count mismatch")
    req(len(fams) >= budget, "successor cannot fill frozen literature budget")
    out = []
    for rank, f in enumerate(fams[:budget], 1):
        req(int(f["rank"]) == rank, "successor rank changed")
        out.append({"family_id": str(f["family_id"]), "event_ids": [str(x) for x in f["event_ids"]]})
    return out


def literature_families(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = [{"family_id": str(f["family_id"]), "event_ids": [str(x) for x in f["member_ids"]]} for f in payload["families"]]
    req(len(out) == int(payload["retained_family_count"]), "literature family count mismatch")
    return out


def metrics(truth: dict[str, str], row_ids: list[str], fams: list[dict[str, Any]]) -> dict[str, Any]:
    req(set(truth) == set(row_ids), "truth universe mismatch")
    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    shower_sets = {label: {eid for eid in row_ids if truth[eid] == label} for label in labels}
    universe = set(row_ids)
    family_sets = [set(f["event_ids"]) & universe for f in fams]
    matrix = np.zeros((len(labels), len(family_sets)))
    for i, label in enumerate(labels):
        s = shower_sets[label]
        for j, f in enumerate(family_sets):
            overlap = len(s & f)
            if overlap:
                matrix[i, j] = 2 * overlap / (len(s) + len(f))
    assigned = np.zeros(len(labels))
    if matrix.shape[1]:
        rows, cols = linear_sum_assignment(-matrix)
        assigned[rows] = matrix[rows, cols]
    return {
        "eligible_known_shower_count": len(labels),
        "family_budget": len(fams),
        "macro_f1": float(np.mean(assigned)),
        "recovered_f1_gt_0_5": int(np.sum(assigned > 0.5)),
        "matched_positive_f1_count": int(np.sum(assigned > 0)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-2013", type=Path, required=True)
    ap.add_argument("--csv-2014", type=Path, required=True)
    ap.add_argument("--mapping-audit", type=Path, required=True)
    ap.add_argument("--evaluator-source", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--comparators", type=Path, required=True)
    ap.add_argument("--matched-pretruth", type=Path, required=True)
    ap.add_argument("--successor-pretruth", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.mapping_audit) == MAP_SHA256, "mapping drift")
    req(sha(a.evaluator_source) == EVALUATOR_SHA256, "evaluator drift")
    matched_freeze_path = a.matched_pretruth / "freeze" / "PRETRUTH_FREEZE.json"
    req(sha(matched_freeze_path) == MATCHED_FREEZE_SHA256, "matched freeze drift")
    matched = load(matched_freeze_path)
    req(matched["pretruth_outputs_frozen"] is True and matched["truth_accessed_before_freeze"] is False, "bad matched pretruth freeze")
    matched_meta = {(str(x["pair"]), int(x["year"])): x for x in matched["panels"]}

    freeze_path = a.successor_pretruth / "PRETRUTH_FREEZE.json"
    freeze = load(freeze_path)
    req(freeze["schema"] == "ORBITTRACE_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH_FREEZE", "wrong successor freeze")
    req(freeze["verdict"] == "PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH", "truth stage opened after failed activation")
    req(freeze["activation_gates_pass"] is True and freeze["direct_physcore_prefix_equivalence"] is True and freeze["all_literature_capacity_gates_pass"] is True, "activation contract failed")
    req(freeze["truth_accessed_before_freeze"] is False and freeze["target_information_access"] is False and freeze["target_region_events_accessed"] is False, "target/truth access before freeze")
    req(freeze["maarsy_scientific_access"] is False and freeze["dms_scientific_access"] is False, "forbidden survey access")
    successor_meta = {(str(x["pair"]), int(x["year"])): x for x in freeze["panels"]}
    req(set(successor_meta) == {(p, y) for p in ("hdbscan", "sugar", "dsh") for y in YEARS}, "successor panel set changed")

    mapping = load(a.mapping_audit)
    csv_bytes = {2013: a.csv_2013.read_bytes(), 2014: a.csv_2014.read_bytes()}
    truth_reader.COMPARATORS.add(DISPLAY["dsh"])
    panels = []

    for pair in PAIRS:
        for year in YEARS:
            budget = EXPECTED_BUDGETS[(pair, year)]
            meta = matched_meta[(pair, year)]
            req(int(meta["literature_family_count"]) == budget, "literature budget drift")
            row_path = a.rows / f"{pair}_{year}.json"
            req(sha(row_path) == str(meta["pairwise_rows_json_sha256"]), f"row drift {pair} {year}")
            rows = load(row_path)
            row_ids = [str(x["id"]) for x in rows]
            panel_path = a.successor_pretruth / "panels" / f"successor_{pair}_{year}.json"
            req(sha(panel_path) == str(successor_meta[(pair, year)]["output_sha256"]), f"successor panel drift {pair} {year}")
            successor_payload = load(panel_path)
            req(successor_payload["truth_accessed"] is False and successor_payload["capacity_ok"] is True, "bad successor panel freeze")
            successor = successor_families(successor_payload, budget)

            lit_path = a.comparators / f"{pair}_{year}" / "comparator_primary_output.json"
            req(sha(lit_path) == str(meta["literature_output_sha256"]), f"literature output drift {pair} {year}")
            literature = literature_families(load(lit_path))
            req(len(literature) == budget, "literature natural budget changed")

            truth_freeze = {
                "year": year,
                "comparator": DISPLAY[pair],
                "pretruth_outputs_frozen": True,
                "truth_accessed_before_freeze": False,
                "target_information_access": False,
                "target_region_access": False,
                "pairwise_event_ids_sha256": meta["pairwise_event_ids_sha256"],
                "orbittrace_primary_output_sha256": successor_meta[(pair, year)]["output_sha256"],
                "comparator_primary_output_sha256": meta["literature_output_sha256"],
                "orbittrace_source_manifest_sha256": sha(freeze_path),
                "comparator_source_manifest_sha256": meta["literature_manifest_sha256"],
            }
            truth, audit = truth_reader.parse_truth_after_freeze(
                csv_bytes[year], year=year, comparator=DISPLAY[pair], requested_event_ids=row_ids,
                mapping_audit=mapping, mapping_audit_sha256=MAP_SHA256,
                pretruth_freeze=truth_freeze, id_prefix=f"SNT{year}"
            )
            sm = metrics(truth, row_ids, successor)
            lm = metrics(truth, row_ids, literature)
            win = sm["macro_f1"] > lm["macro_f1"] and sm["recovered_f1_gt_0_5"] >= lm["recovered_f1_gt_0_5"]
            panels.append({
                "pair": pair,
                "literature_method": DISPLAY[pair],
                "year": year,
                "literature_budget": budget,
                "successor": sm,
                "literature": lm,
                "win": bool(win),
                "truth_audit": audit,
            })

    inherited = []
    for year in YEARS:
        x = INHERITED[year]
        win = x["successor_macro_f1"] > x["published_hdbscan_macro_f1"] and x["successor_recovered"] >= x["published_hdbscan_recovered"]
        inherited.append({"pair": "hdbscan", "year": year, **x, "win": bool(win), "truth_reopened": False})

    all_wins = all(x["win"] for x in inherited) and all(x["win"] for x in panels)
    verdict = "PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1" if all_wins else "FAIL_PHYSCORE_RESIDUAL_TOPOMODAL_V1"
    out = {
        "schema": "ORBITTRACE_PHYSCORE_RESIDUAL_TOPOMODAL_V1_RESULT",
        "scientific_role": "EXPOSED_SONOTACO_DEVELOPMENT_ONLY",
        "method": "PhysCore-Residual TopoModal v1",
        "verdict": verdict,
        "inherited_published_hdbscan_panels": inherited,
        "new_matched_literature_panels": panels,
        "panel_wins": sum(x["win"] for x in inherited) + sum(x["win"] for x in panels),
        "panel_count": 6,
        "pretruth_freeze_sha256": sha(freeze_path),
        "truth_access_before_pretruth": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "RESULT.json", out)
    print(json.dumps({
        "verdict": verdict,
        "wins": out["panel_wins"],
        "result_sha256": result_sha,
        "panels": [{"pair": x["pair"], "year": x["year"], "successor_f1": x["successor"]["macro_f1"], "literature_f1": x["literature"]["macro_f1"], "successor_recovered": x["successor"]["recovered_f1_gt_0_5"], "literature_recovered": x["literature"]["recovered_f1_gt_0_5"], "win": x["win"]} for x in panels]
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
