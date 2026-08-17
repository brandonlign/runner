#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_final_sonotaco_truth_v1 import truth_boundary as truth_reader

PAIRS = ("sugar", "hdbscan", "dsh")
YEARS = (2013, 2014)
DISPLAY = {
    "sugar": "Sugar",
    "hdbscan": "catalogue HDBSCAN",
    "dsh": "Rudawska-Jenniskens D_SH single linkage",
}
EXPECTED_EVALUATOR_SHA256 = "cefcc8900a7b3d083f81148427e9f80e2c7192bb25dd9bb635e6677aa23a555c"
EXPECTED_MAPPING_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def candidate_families(payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    fams = payload.get("families")
    require(isinstance(fams, list) and fams, "empty flagship family list")
    order: list[str] = []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for expected_rank, f in enumerate(fams, 1):
        fid = str(f["family_id"]); require(fid not in seen, "duplicate flagship family")
        require(int(f["rank"]) == expected_rank, "flagship rank/order changed")
        ids = [str(x) for x in f["event_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid flagship membership")
        seen.add(fid); order.append(fid); out.append({"family_id": fid, "event_ids": ids})
    require(int(payload["family_count"]) == len(out), "flagship family_count changed")
    return order, out


def literature_families(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fams = payload.get("families")
    require(isinstance(fams, list), "invalid literature family list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for f in fams:
        fid = str(f["family_id"]); require(fid and fid not in seen, "duplicate literature family")
        ids = [str(x) for x in f["member_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid literature membership")
        seen.add(fid); out.append({"family_id": fid, "event_ids": ids})
    require(int(payload["retained_family_count"]) == len(out), "literature family_count changed")
    return out


def matched_metrics(
    *,
    truth: dict[str, str],
    row_ids: list[str],
    families: list[dict[str, Any]],
) -> dict[str, Any]:
    row_set = set(row_ids)
    require(set(truth) == row_set, "truth universe differs from row universe")
    known_counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in known_counts.items() if n >= 4)
    require(labels, "no eligible known showers")
    shower_sets = {lab: {eid for eid in row_ids if truth[eid] == lab} for lab in labels}
    family_sets = [set(f["event_ids"]) & row_set for f in families]
    matrix = np.zeros((len(labels), len(family_sets)), dtype=np.float64)
    for i, lab in enumerate(labels):
        s = shower_sets[lab]
        for j, fam in enumerate(family_sets):
            if not fam:
                continue
            inter = len(s & fam)
            if inter:
                matrix[i, j] = 2.0 * inter / (len(s) + len(fam))
    assigned = np.zeros(len(labels), dtype=np.float64)
    if matrix.shape[1] > 0:
        rr, cc = linear_sum_assignment(-matrix)
        assigned[rr] = matrix[rr, cc]
    first = {labels[i]: float(assigned[i]) for i in range(len(labels))}
    return {
        "eligible_known_shower_count": len(labels),
        "family_budget": len(families),
        "macro_f1": float(np.mean(assigned)),
        "recovered_f1_gt_0_5": int(np.sum(assigned > 0.5)),
        "matched_positive_f1_count": int(np.sum(assigned > 0.0)),
        "assigned_f1_by_label": first,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-2013", type=Path, required=True)
    ap.add_argument("--csv-2014", type=Path, required=True)
    ap.add_argument("--mapping-audit", type=Path, required=True)
    ap.add_argument("--evaluator-source", type=Path, required=True)
    ap.add_argument("--prepare-dir", type=Path, required=True)
    ap.add_argument("--freeze-file", type=Path, required=True)
    for pair in PAIRS:
        ap.add_argument(f"--candidate-{pair}-dir", type=Path, required=True)
        for year in YEARS:
            ap.add_argument(f"--comparator-{pair}-{year}-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.mapping_audit) == EXPECTED_MAPPING_SHA256, "truth mapping audit identity changed")
    require(sha(a.evaluator_source) == EXPECTED_EVALUATOR_SHA256, "exact evaluator source identity changed")
    exact_evaluator = load_module(a.evaluator_source, "exact_final_matched_evaluator")
    mapping_audit = load(a.mapping_audit)
    freeze = load(a.freeze_file)
    require(freeze.get("pretruth_outputs_frozen") is True, "pretruth freeze missing")
    require(freeze.get("truth_accessed_before_freeze") is False, "truth accessed before freeze")
    freeze_index = {(str(p["pair"]), int(p["year"])): p for p in freeze["panels"]}
    require(set(freeze_index) == {(p, y) for p in PAIRS for y in YEARS}, "frozen panel set changed")

    # The frozen truth parser has an allowlist for the two original comparators. Extending
    # only that validation allowlist lets the identical parser handle the newly frozen D_SH
    # row universe; parsing/mapping logic itself remains byte-identical.
    truth_reader.COMPARATORS.add(DISPLAY["dsh"])
    csvs = {2013: a.csv_2013.read_bytes(), 2014: a.csv_2014.read_bytes()}
    candidate_dirs = {p: getattr(a, f"candidate_{p}_dir") for p in PAIRS}
    comp_dirs = {(p, y): getattr(a, f"comparator_{p}_{y}_dir") for p in PAIRS for y in YEARS}

    panels: list[dict[str, Any]] = []
    for pair in PAIRS:
        cand_path = candidate_dirs[pair] / "candidate_primary_output.json"
        cand_manifest = candidate_dirs[pair] / "candidate_source_manifest.json"
        cand = load(cand_path)
        cand_order, cand_all = candidate_families(cand)
        for year in YEARS:
            frozen = freeze_index[(pair, year)]
            rows_path = a.prepare_dir / f"{pair}_{year}.json"
            rows = load(rows_path)
            row_ids = [str(r["id"]) for r in rows]
            require(len(row_ids) == len(set(row_ids)), "duplicate evaluation row IDs")
            require(sha(rows_path) == frozen["pairwise_rows_json_sha256"], "rows changed after freeze")
            require(sha(cand_path) == frozen["topomodal_primary_output_sha256"], "flagship output changed after freeze")
            require(sha(cand_manifest) == frozen["topomodal_source_manifest_sha256"], "flagship source manifest changed")

            comp_path = comp_dirs[(pair, year)] / "comparator_primary_output.json"
            comp_manifest = comp_dirs[(pair, year)] / "comparator_source_manifest.json"
            require(sha(comp_path) == frozen["literature_primary_output_sha256"], "literature output changed after freeze")
            require(sha(comp_manifest) == frozen["literature_source_manifest_sha256"], "literature source manifest changed")
            comp = load(comp_path)
            lit_all = literature_families(comp)
            B = len(lit_all)
            require(B == int(frozen["literature_family_count"]) and B > 0, "frozen literature budget changed")
            topo_budget = cand_all[:min(B, len(cand_all))]

            truth_freeze = {
                "year": year,
                "comparator": DISPLAY[pair],
                "pretruth_outputs_frozen": True,
                "truth_accessed_before_freeze": False,
                "target_information_access": False,
                "target_region_access": False,
                "pairwise_event_ids_sha256": frozen["pairwise_event_ids_sha256"],
                "orbittrace_primary_output_sha256": frozen["topomodal_primary_output_sha256"],
                "comparator_primary_output_sha256": frozen["literature_primary_output_sha256"],
                "orbittrace_source_manifest_sha256": frozen["topomodal_source_manifest_sha256"],
                "comparator_source_manifest_sha256": frozen["literature_source_manifest_sha256"],
            }
            truth, truth_audit = truth_reader.parse_truth_after_freeze(
                csvs[year], year=year, comparator=DISPLAY[pair], requested_event_ids=row_ids,
                mapping_audit=mapping_audit, mapping_audit_sha256=EXPECTED_MAPPING_SHA256,
                pretruth_freeze=truth_freeze, id_prefix=f"SNT{year}",
            )

            topo_m = matched_metrics(truth=truth, row_ids=row_ids, families=topo_budget)
            lit_m = matched_metrics(truth=truth, row_ids=row_ids, families=lit_all)
            require(topo_m["eligible_known_shower_count"] == lit_m["eligible_known_shower_count"], "eligible truth universe mismatch")

            exact_payload = {
                "year": year,
                "comparator_id": DISPLAY[pair],
                "row_ids": row_ids,
                "row_truth": truth,
                "candidate_order": cand_order,
                "candidate_families": cand_all,
                "comparator_families": lit_all,
            }
            exact_output = exact_evaluator.evaluate_pair(exact_payload)

            win = (
                float(topo_m["macro_f1"]) > float(lit_m["macro_f1"])
                and int(topo_m["recovered_f1_gt_0_5"]) >= int(lit_m["recovered_f1_gt_0_5"])
            )
            panel = {
                "pair": pair,
                "literature_method": DISPLAY[pair],
                "year": year,
                "event_count": len(row_ids),
                "budget": B,
                "topomodal_candidate_capacity": len(cand_all),
                "topomodal": topo_m,
                "literature": lit_m,
                "topomodal_win": bool(win),
                "exact_frozen_evaluator_output": exact_output,
                "truth_audit": truth_audit,
            }
            dump(a.output / f"panel_{pair}_{year}.json", panel)
            panels.append(panel)

    require(len(panels) == 6, "expected six evaluated panels")
    wins = sum(bool(p["topomodal_win"]) for p in panels)
    verdict = "PASS_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_V1" if wins == 6 else "FAIL_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_V1"
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_RESULT_V1",
        "scientific_role": "EXPOSED_POST_SELECTION_SONOTACO_2013_2014_LITERATURE_BENCHMARK",
        "flagship_method": "fixed-scale TopoModal",
        "comparators": [DISPLAY[p] for p in PAIRS],
        "years": list(YEARS),
        "panel_wins": wins,
        "panel_count": len(panels),
        "verdict": verdict,
        "panels": panels,
        "pretruth_freeze_sha256": sha(a.freeze_file),
        "evaluator_source_sha256": EXPECTED_EVALUATOR_SHA256,
        "mapping_audit_sha256": EXPECTED_MAPPING_SHA256,
        "blind_exclusion": [20.0, 55.0],
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY",
        "truth_access_before_pretruth": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "TOPOMODAL_FLAGSHIP_MATCHED_LITERATURE_RESULT_V1.json", result)
    print(json.dumps({"verdict": verdict, "panel_wins": wins, "panel_count": len(panels), "result_sha256": result_sha}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
