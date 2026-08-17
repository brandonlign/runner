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

YEARS = (2013, 2014)
METHOD = "OrbitTrace Compact Mixture v1"
LITERATURE = "catalogue HDBSCAN"
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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def candidate_families(payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    require(payload.get("method") == METHOD, "wrong candidate method")
    fams = payload.get("families")
    require(isinstance(fams, list) and fams, "empty candidate family list")
    out: list[dict[str, Any]] = []
    order: list[str] = []
    seen: set[str] = set()
    for expected_rank, f in enumerate(fams, 1):
        fid = str(f["family_id"])
        require(fid and fid not in seen, "duplicate candidate family")
        require(int(f["rank"]) == expected_rank, "candidate rank changed")
        ids = [str(x) for x in f["event_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid candidate membership")
        require(int(f["member_count"]) == len(ids), "candidate member_count mismatch")
        seen.add(fid)
        order.append(fid)
        out.append({"family_id": fid, "event_ids": ids})
    require(int(payload["family_count"]) == len(out), "candidate family_count changed")
    return order, out


def literature_families(payload: dict[str, Any]) -> list[dict[str, Any]]:
    require(payload.get("method") == LITERATURE, "wrong HDBSCAN method")
    fams = payload.get("families")
    require(isinstance(fams, list) and fams, "empty HDBSCAN family list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for f in fams:
        fid = str(f["family_id"])
        require(fid and fid not in seen, "duplicate HDBSCAN family")
        ids = [str(x) for x in f["member_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid HDBSCAN membership")
        seen.add(fid)
        out.append({"family_id": fid, "event_ids": ids})
    require(int(payload["retained_family_count"]) == len(out), "HDBSCAN family_count changed")
    return out


def matched_metrics(*, truth: dict[str, str], row_ids: list[str], families: list[dict[str, Any]]) -> dict[str, Any]:
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
    return {
        "eligible_known_shower_count": len(labels),
        "family_budget": len(families),
        "macro_f1": float(np.mean(assigned)),
        "recovered_f1_gt_0_5": int(np.sum(assigned > 0.5)),
        "matched_positive_f1_count": int(np.sum(assigned > 0.0)),
        "assigned_f1_by_label": {labels[i]: float(assigned[i]) for i in range(len(labels))},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-2013", type=Path, required=True)
    ap.add_argument("--csv-2014", type=Path, required=True)
    ap.add_argument("--mapping-audit", type=Path, required=True)
    ap.add_argument("--evaluator-source", type=Path, required=True)
    ap.add_argument("--prepare-dir", type=Path, required=True)
    ap.add_argument("--freeze-file", type=Path, required=True)
    ap.add_argument("--candidate-dir", type=Path, required=True)
    ap.add_argument("--hdbscan-2013-dir", type=Path, required=True)
    ap.add_argument("--hdbscan-2014-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.mapping_audit) == EXPECTED_MAPPING_SHA256, "truth mapping audit identity changed")
    require(sha(a.evaluator_source) == EXPECTED_EVALUATOR_SHA256, "exact evaluator source identity changed")
    exact_evaluator = load_module(a.evaluator_source, "exact_final_matched_evaluator")
    mapping_audit = load(a.mapping_audit)
    freeze = load(a.freeze_file)
    require(freeze.get("pretruth_outputs_frozen") is True, "pretruth freeze missing")
    require(freeze.get("truth_accessed_before_freeze") is False, "truth accessed before pretruth freeze")
    require(freeze.get("target_information_access") is False, "target information entered freeze")
    require(freeze.get("post_result_parameter_search") is False, "post-result search in freeze")
    frozen = {int(p["year"]): p for p in freeze["panels"]}
    require(set(frozen) == set(YEARS), "frozen year set changed")

    cand_path = a.candidate_dir / "candidate_primary_output.json"
    cand_manifest_path = a.candidate_dir / "candidate_source_manifest.json"
    candidate = load(cand_path)
    cand_order, cand_all = candidate_families(candidate)
    csvs = {2013: a.csv_2013.read_bytes(), 2014: a.csv_2014.read_bytes()}
    hdirs = {2013: a.hdbscan_2013_dir, 2014: a.hdbscan_2014_dir}
    panels: list[dict[str, Any]] = []

    for year in YEARS:
        fr = frozen[year]
        rows_path = a.prepare_dir / f"hdbscan_{year}.json"
        rows = load(rows_path)
        row_ids = [str(r["id"]) for r in rows]
        require(len(row_ids) == len(set(row_ids)), "duplicate evaluation row IDs")
        require(sha(rows_path) == fr["rows_json_sha256"], "row universe changed after freeze")
        require(sha(cand_path) == fr["candidate_primary_output_sha256"], "candidate output changed after freeze")
        require(sha(cand_manifest_path) == fr["candidate_source_manifest_sha256"], "candidate manifest changed after freeze")

        hdir = hdirs[year]
        hpath = hdir / "comparator_primary_output.json"
        hm_path = hdir / "comparator_source_manifest.json"
        hs_path = hdir / "comparator_pretruth_summary.json"
        require(sha(hpath) == fr["hdbscan_primary_output_sha256"], "HDBSCAN output changed after freeze")
        require(sha(hm_path) == fr["hdbscan_source_manifest_sha256"], "HDBSCAN manifest changed after freeze")
        require(sha(hs_path) == fr["hdbscan_pretruth_summary_sha256"], "HDBSCAN summary changed after freeze")
        hdb = load(hpath)
        lit_all = literature_families(hdb)
        B = len(lit_all)
        require(B == int(fr["hdbscan_family_budget"]) and B > 0, "frozen HDBSCAN budget changed")
        require(len(cand_all) >= B, "candidate capacity below HDBSCAN budget")
        cand_budget = cand_all[:B]

        truth_freeze = {
            "year": year,
            "comparator": LITERATURE,
            "pretruth_outputs_frozen": True,
            "truth_accessed_before_freeze": False,
            "target_information_access": False,
            "target_region_access": False,
            "pairwise_event_ids_sha256": fr["event_ids_sha256"],
            "orbittrace_primary_output_sha256": fr["candidate_primary_output_sha256"],
            "comparator_primary_output_sha256": fr["hdbscan_primary_output_sha256"],
            "orbittrace_source_manifest_sha256": fr["candidate_source_manifest_sha256"],
            "comparator_source_manifest_sha256": fr["hdbscan_source_manifest_sha256"],
        }
        truth, truth_audit = truth_reader.parse_truth_after_freeze(
            csvs[year], year=year, comparator=LITERATURE, requested_event_ids=row_ids,
            mapping_audit=mapping_audit, mapping_audit_sha256=EXPECTED_MAPPING_SHA256,
            pretruth_freeze=truth_freeze, id_prefix=f"SNT{year}",
        )
        cand_m = matched_metrics(truth=truth, row_ids=row_ids, families=cand_budget)
        hdb_m = matched_metrics(truth=truth, row_ids=row_ids, families=lit_all)
        require(cand_m["eligible_known_shower_count"] == hdb_m["eligible_known_shower_count"], "eligible truth universe mismatch")

        exact_payload = {
            "year": year, "comparator_id": LITERATURE, "row_ids": row_ids, "row_truth": truth,
            "candidate_order": cand_order, "candidate_families": cand_all, "comparator_families": lit_all,
        }
        exact_output = exact_evaluator.evaluate_pair(exact_payload)
        win = (
            float(cand_m["macro_f1"]) > float(hdb_m["macro_f1"])
            and int(cand_m["recovered_f1_gt_0_5"]) >= int(hdb_m["recovered_f1_gt_0_5"])
        )
        panel = {
            "year": year, "event_count": len(row_ids), "budget": B, "candidate_capacity": len(cand_all),
            "compact_mixture": cand_m, "published_hdbscan": hdb_m, "compact_mixture_win": bool(win),
            "exact_frozen_evaluator_output": exact_output, "truth_audit": truth_audit,
        }
        dump(a.output / f"panel_{year}.json", panel)
        panels.append(panel)

    wins = sum(bool(p["compact_mixture_win"]) for p in panels)
    verdict = "PASS_COMPACT_MIXTURE_V1_HDBSCAN_DEVELOPMENT" if wins == 2 else "FAIL_COMPACT_MIXTURE_V1_HDBSCAN_DEVELOPMENT"
    result = {
        "schema": "ORBITTRACE_COMPACT_MIXTURE_V1_HDBSCAN_DEVELOPMENT_RESULT",
        "scientific_role": "EXPOSED_POST_SELECTION_SONOTACO_2013_2014_DEVELOPMENT",
        "method": METHOD, "literature_comparator": LITERATURE, "panel_wins": wins,
        "panel_count": len(panels), "verdict": verdict, "panels": panels,
        "pretruth_freeze_sha256": sha(a.freeze_file), "evaluator_source_sha256": EXPECTED_EVALUATOR_SHA256,
        "mapping_audit_sha256": EXPECTED_MAPPING_SHA256, "blind_exclusion": [20.0, 55.0],
        "sonotaco_role": "EXPOSED_DEVELOPMENT_ONLY", "truth_access_before_pretruth": False,
        "target_information_access": False, "target_region_events_accessed": False,
        "maarsy_scientific_access": False, "dms_scientific_access": False, "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "COMPACT_MIXTURE_V1_HDBSCAN_RESULT.json", result)
    print(json.dumps({
        "verdict": verdict, "panel_wins": wins, "panel_count": len(panels), "result_sha256": result_sha,
        "panels": [{
            "year": p["year"], "candidate_macro_f1": p["compact_mixture"]["macro_f1"],
            "hdbscan_macro_f1": p["published_hdbscan"]["macro_f1"],
            "candidate_recovered": p["compact_mixture"]["recovered_f1_gt_0_5"],
            "hdbscan_recovered": p["published_hdbscan"]["recovered_f1_gt_0_5"],
            "win": p["compact_mixture_win"],
        } for p in panels],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
