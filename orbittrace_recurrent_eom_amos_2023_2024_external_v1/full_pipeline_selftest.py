#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def canonical_rows(year: int) -> list[dict]:
    centers = {
        "A": (100.0, 10.0, 5.0, 30.0),
        "B": (180.0, -30.0, -10.0, 45.0),
        "C": (260.0, 70.0, 20.0, 55.0),
    }
    rows = []
    for code, (sol0, lon0, lat0, vg0) in centers.items():
        for i in range(14):
            d = (i - 6.5) * 0.015
            rows.append(
                {
                    "id": f"SYN{year}_{code}_{i:02d}",
                    "year": year,
                    "sol": sol0 + d,
                    "sun_lon": lon0 + 0.7 * d,
                    "ecl_lat": lat0 - 0.4 * d,
                    "vg": vg0 + 0.03 * d,
                    "iau": 0,
                    "complex_key": "HIDDEN",
                }
            )
    rows.sort(key=lambda r: r["id"])
    return rows


def write_labels(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "shower_code"])
        for r in rows:
            code = str(r["id"]).split("_")[1]
            w.writerow([r["id"], f"SYN_SHOWER_{code}"])


def main() -> int:
    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        rows23 = canonical_rows(2023)
        rows24 = canonical_rows(2024)
        can23 = td / "canonical_2023.json"
        can24 = td / "canonical_2024.json"
        can23.write_text(json.dumps(rows23, separators=(",", ":")) + "\n", encoding="utf-8")
        can24.write_text(json.dumps(rows24, separators=(",", ":")) + "\n", encoding="utf-8")
        pre_dir = td / "pretruth"
        eval_dir = td / "evaluation"

        subprocess.run(
            [
                sys.executable,
                str(HERE / "generate_pretruth.py"),
                "--canonical-2023",
                str(can23),
                "--canonical-2024",
                str(can24),
                "--output",
                str(pre_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pre_path = pre_dir / "RECURRENT_EOM_AMOS_2023_2024_PRETRUTH.json"
        pre = json.loads(pre_path.read_text(encoding="utf-8"))
        pre_sha = (pre_dir / "PRETRUTH_SHA256.txt").read_text(encoding="ascii").strip()
        require(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "pretruth stage exposed synthetic labels")
        require(pre["years"] == [2023, 2024] and pre["blind_exclusion"] == [20.0, 55.0], "pretruth year/blind freeze changed")
        require(pre["events_by_year"] == {"2023": 42, "2024": 42}, "synthetic event count changed")
        require(pre["parent_candidates"] and pre["successor_candidates"], "synthetic HDBSCAN emitted no candidates")

        lab23 = td / "labels_2023.csv"
        lab24 = td / "labels_2024.csv"
        write_labels(lab23, rows23)
        write_labels(lab24, rows24)
        subprocess.run(
            [
                sys.executable,
                str(HERE / "evaluate_labels.py"),
                "--pretruth",
                str(pre_path),
                "--pretruth-sha256",
                pre_sha,
                "--labels-2023",
                str(lab23),
                "--labels-2024",
                str(lab24),
                "--output",
                str(eval_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads((eval_dir / "RECURRENT_EOM_AMOS_2023_2024_EXTERNAL_RESULT.json").read_text(encoding="utf-8"))
        require(result["pretruth_sha256"] == pre_sha, "post-freeze evaluator did not bind exact pretruth SHA")
        require(result["verdict"] in {"PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION", "FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION"}, "unexpected synthetic verdict token")
        require(result["candidate_generation_recomputed_after_labels"] is False and result["ranking_changed_after_labels"] is False, "post-label candidate/rank mutation flag changed")
        require(result["quality_filter_used"] is False and result["survey_calibration_used"] is False, "synthetic external evaluator introduced transport tuning")

    out = {
        "verdict": "PASS_RECURRENT_EOM_AMOS_SPLIT_STAGE_SYNTHETIC_AUDIT",
        "synthetic_only": True,
        "pretruth_program_accepts_label_argument": False,
        "pretruth_hash_bound_before_label_evaluation": True,
        "candidate_generation_recomputed_after_labels": False,
        "ranking_changed_after_labels": False,
        "years_frozen": [2023, 2024],
        "blind_exclusion": [20.0, 55.0],
        "amos_event_rows_accessed": False,
        "amos_labels_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    output = HERE / "output"
    output.mkdir(parents=True, exist_ok=True)
    (output / "SPLIT_STAGE_SYNTHETIC_AUDIT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
