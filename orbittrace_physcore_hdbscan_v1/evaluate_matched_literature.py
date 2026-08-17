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

PAIRS = ("sugar", "hdbscan", "dsh")
YEARS = (2013, 2014)
DISPLAY = {
    "sugar": "Sugar",
    "hdbscan": "catalogue HDBSCAN",
    "dsh": "Rudawska-Jenniskens D_SH single linkage",
}
EXPECTED_MAPPING_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
FROZEN_PHYSCORE_GIT_BLOB_SHA1 = "410a5ebe1ffdcf88f1530a2eb61f6342ca3639dd"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, value: Any) -> str:
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def candidate_families(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fams = payload.get("families")
    require(isinstance(fams, list) and fams, "empty PhysCore family list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for expected_rank, family in enumerate(fams, 1):
        fid = str(family["family_id"])
        require(fid not in seen, "duplicate PhysCore family")
        require(int(family["rank"]) == expected_rank, "PhysCore rank/order changed")
        ids = [str(x) for x in family["event_ids"]]
        require(ids and len(ids) == len(set(ids)), "invalid PhysCore membership")
        seen.add(fid)
        out.append({"family_id": fid, "event_ids": ids})
    require(int(payload["family_count"]) == len(out), "PhysCore family_count changed")
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
        shower = shower_sets[lab]
        for j, family in enumerate(family_sets):
            if not family:
                continue
            inter = len(shower & family)
            if inter:
                matrix[i, j] = 2.0 * inter / (len(shower) + len(family))
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
    ap.add_argument("--prepare-dir", type=Path, required=True)
    ap.add_argument("--old-freeze", type=Path, required=True)
    ap.add_argument("--binding-result", type=Path, required=True)
    ap.add_argument("--physcore-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.mapping_audit) == EXPECTED_MAPPING_SHA256, "truth mapping audit identity changed")
    mapping_audit = load(a.mapping_audit)
    old_freeze = load(a.old_freeze)
    binding = load(a.binding_result)
    freeze_index = {(str(p["pair"]), int(p["year"])): p for p in old_freeze["panels"]}
    binding_index = {(str(p["pair"]), int(p["year"])): p for p in binding["panels"]}
    expected_keys = {(p, y) for p in PAIRS for y in YEARS}
    require(set(freeze_index) == expected_keys and set(binding_index) == expected_keys, "binding panel set changed")
    require(old_freeze.get("pretruth_outputs_frozen") is True, "old literature freeze missing")
    require(old_freeze.get("truth_accessed_before_freeze") is False, "old literature truth ordering changed")

    truth_reader.COMPARATORS.add(DISPLAY["dsh"])
    csvs = {2013: a.csv_2013.read_bytes(), 2014: a.csv_2014.read_bytes()}
    panels: list[dict[str, Any]] = []
    frozen_source_sha256s: set[str] = set()

    for pair in PAIRS:
        for year in YEARS:
            rows_path = a.prepare_dir / f"{pair}_{year}.json"
            rows = load(rows_path)
            row_ids = [str(r["id"]) for r in rows]
            require(len(row_ids) == len(set(row_ids)), "duplicate evaluation row IDs")
            frozen = freeze_index[(pair, year)]
            require(sha(rows_path) == frozen["pairwise_rows_json_sha256"], "matched row universe changed")

            panel_dir = a.physcore_root / f"{pair}-{year}"
            pc_path = panel_dir / "physcore_primary_output.json"
            manifest_path = panel_dir / "physcore_source_manifest.json"
            pc = load(pc_path)
            manifest = load(manifest_path)
            require(pc["method"] == "PhysCore-HDBSCAN v1" and pc["pair"] == pair and int(pc["year"]) == year, "wrong PhysCore panel")
            require(pc["frozen_physcore_source_git_blob_sha1"] == FROZEN_PHYSCORE_GIT_BLOB_SHA1, "PhysCore blob identity changed")
            require(manifest["frozen_physcore_source_git_blob_sha1"] == FROZEN_PHYSCORE_GIT_BLOB_SHA1, "PhysCore manifest blob identity changed")
            require(pc["frozen_physcore_source_sha256"] == manifest["frozen_physcore_source_sha256"], "PhysCore source SHA-256 mismatch")
            frozen_source_sha256s.add(str(pc["frozen_physcore_source_sha256"]))
            require(pc["row_json_sha256"] == sha(rows_path), "PhysCore rows changed")
            require(manifest["candidate_output_sha256"] == sha(pc_path), "PhysCore candidate hash mismatch")
            require(pc.get("truth_accessed") is False and manifest.get("truth_accessed") is False, "truth accessed during PhysCore generation")
            require(pc.get("post_result_parameter_search") is False and manifest.get("post_result_parameter_search") is False, "post-result search detected")
            if pair == "hdbscan":
                require(pc["hdbscan_primary_output_sha256"] == frozen["literature_primary_output_sha256"], "HDBSCAN parent does not reproduce binding comparator")
                require(pc["hdbscan_source_manifest_sha256"] == frozen["literature_source_manifest_sha256"], "HDBSCAN parent manifest does not reproduce binding comparator")

            truth_freeze = {
                "year": year,
                "comparator": DISPLAY[pair],
                "pretruth_outputs_frozen": True,
                "truth_accessed_before_freeze": False,
                "target_information_access": False,
                "target_region_access": False,
                "pairwise_event_ids_sha256": frozen["pairwise_event_ids_sha256"],
                "orbittrace_primary_output_sha256": sha(pc_path),
                "comparator_primary_output_sha256": frozen["literature_primary_output_sha256"],
                "orbittrace_source_manifest_sha256": sha(manifest_path),
                "comparator_source_manifest_sha256": frozen["literature_source_manifest_sha256"],
            }
            truth, truth_audit = truth_reader.parse_truth_after_freeze(
                csvs[year], year=year, comparator=DISPLAY[pair], requested_event_ids=row_ids,
                mapping_audit=mapping_audit, mapping_audit_sha256=EXPECTED_MAPPING_SHA256,
                pretruth_freeze=truth_freeze, id_prefix=f"SNT{year}",
            )
            phys = matched_metrics(truth=truth, row_ids=row_ids, families=candidate_families(pc))
            bound_panel = binding_index[(pair, year)]
            literature = bound_panel["literature"]
            require(int(bound_panel["event_count"]) == len(row_ids), "binding event count changed")
            require(int(literature["eligible_known_shower_count"]) == int(phys["eligible_known_shower_count"]), "eligible truth universe changed")
            win = (
                float(phys["macro_f1"]) > float(literature["macro_f1"])
                and int(phys["recovered_f1_gt_0_5"]) >= int(literature["recovered_f1_gt_0_5"])
            )
            panel = {
                "pair": pair,
                "literature_method": DISPLAY[pair],
                "year": year,
                "event_count": len(row_ids),
                "physcore": phys,
                "literature": literature,
                "physcore_win": bool(win),
                "truth_audit": truth_audit,
                "physcore_primary_output_sha256": sha(pc_path),
                "physcore_source_manifest_sha256": sha(manifest_path),
            }
            dump(a.output / f"panel_{pair}_{year}.json", panel)
            panels.append(panel)

    require(len(frozen_source_sha256s) == 1, "PhysCore source bytes differ across panels")
    frozen_source_sha256 = next(iter(frozen_source_sha256s))
    require(len(panels) == 6, "expected six evaluated panels")
    wins = sum(bool(p["physcore_win"]) for p in panels)
    verdict = "PASS_PHYSCORE_HDBSCAN_V1_MATCHED_LITERATURE" if wins == 6 else "FAIL_PHYSCORE_HDBSCAN_V1_MATCHED_LITERATURE"
    result = {
        "schema": "ORBITTRACE_PHYSCORE_HDBSCAN_V1_MATCHED_LITERATURE_RESULT",
        "scientific_role": "EXPOSED_POST_SELECTION_SONOTACO_2013_2014_LITERATURE_BENCHMARK",
        "method": "PhysCore-HDBSCAN v1",
        "comparators": [DISPLAY[p] for p in PAIRS],
        "years": list(YEARS),
        "panel_wins": wins,
        "panel_count": 6,
        "verdict": verdict,
        "panels": panels,
        "frozen_physcore_source_git_blob_sha1": FROZEN_PHYSCORE_GIT_BLOB_SHA1,
        "frozen_physcore_source_sha256": frozen_source_sha256,
        "binding_literature_result_sha256": sha(a.binding_result),
        "old_literature_freeze_sha256": sha(a.old_freeze),
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
    result_sha = dump(a.output / "PHYSCORE_HDBSCAN_V1_MATCHED_LITERATURE_RESULT.json", result)
    print(json.dumps({"verdict": verdict, "panel_wins": wins, "panel_count": 6, "result_sha256": result_sha}, indent=2, sort_keys=True))
    for p in panels:
        print(p["pair"], p["year"], "WIN" if p["physcore_win"] else "LOSS", p["physcore"]["macro_f1"], p["literature"]["macro_f1"], p["physcore"]["recovered_f1_gt_0_5"], p["literature"]["recovered_f1_gt_0_5"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
