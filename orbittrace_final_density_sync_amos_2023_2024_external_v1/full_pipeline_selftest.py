#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PRIMARY = {
    "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
    "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION",
}
INCREMENTAL = {
    "PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
    "NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS",
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def make_provider_files(root: Path, year: int) -> tuple[Path, Path, dict[str, str]]:
    index_rows: list[list[object]] = []
    geometry_rows: list[list[object]] = []
    labels: dict[str, str] = {}
    clusters = [
        (100.0, 250.0, -20.0, 31.0, "SYN_A"),
        (150.0, 120.0, 35.0, 42.0, "SYN_B"),
        (220.0, 40.0, -5.0, 55.0, "SYN_C"),
        (300.0, 315.0, 15.0, 24.0, "SYN_D"),
    ]
    n = 0
    for cidx, (sol0, ra0, dec0, vg0, label) in enumerate(clusters):
        for j in range(16):
            eid = f"{year}-SYN-{cidx}-{j:03d}"
            sol = sol0 + (j - 7.5) * 0.015 + (year - 2023) * 0.003
            ra = ra0 + (j - 7.5) * 0.02
            dec = dec0 + ((j % 5) - 2) * 0.02
            vg = vg0 + ((j % 7) - 3) * 0.008
            index_rows.append([eid, f"{year}-06-01T00:{n%60:02d}:00Z", f"{sol:.9f}"])
            geometry_rows.append([eid, f"{ra:.9f}", f"{dec:.9f}", f"{vg:.9f}"])
            labels[eid] = label
            n += 1
    for j in range(16):
        eid = f"{year}-BG-{j:03d}"
        sol = 70.0 + j * 17.0
        if 20.0 <= sol <= 55.0:
            sol = 60.0 + j
        ra = (17.0 * j + 5.0) % 360.0
        dec = -55.0 + 7.0 * (j % 15)
        vg = 18.0 + 2.2 * j
        index_rows.append([eid, f"{year}-07-01T01:{n%60:02d}:00Z", f"{sol:.9f}"])
        geometry_rows.append([eid, f"{ra:.9f}", f"{dec:.9f}", f"{vg:.9f}"])
        labels[eid] = "SPORADIC"
        n += 1
    protected = f"{year}-PROTECTED-SYN"
    index_rows.append([protected, f"{year}-08-01T00:00:00Z", "30.000000000"])

    index_path = root / f"index_{year}.csv"
    geom_path = root / f"geometry_{year}.csv"
    write_csv(index_path, ["event_id", "utc_time", "solar_longitude_deg"], index_rows)
    write_csv(geom_path, ["event_id", "ra_j2000_deg", "dec_j2000_deg", "vg_km_s"], geometry_rows)
    return index_path, geom_path, labels


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--generator", type=Path, required=True)
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--amos-infra", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.mkdir(parents=True, exist_ok=True)

    adapter_dir = a.amos_infra / "orbittrace_recurrent_eom_amos_2023_2024_external_v1" / "adapter"
    adapt = adapter_dir / "adapt.py"
    transform = adapter_dir / "transform.py"
    require(adapt.exists() and transform.exists(), "exact audited AMOS adapter sources missing")

    canon: dict[int, Path] = {}
    all_labels: dict[int, dict[str, str]] = {}
    for year in (2023, 2024):
        index_path, geom_path, labels = make_provider_files(a.work, year)
        all_labels[year] = labels
        canon[year] = a.work / f"canonical_{year}.json"
        run([
            sys.executable,
            str(adapt.resolve()),
            "--index", str(index_path.resolve()),
            "--geometry", str(geom_path.resolve()),
            "--year", str(year),
            "--output", str(canon[year].resolve()),
        ], cwd=adapter_dir)
        rows = json.loads(canon[year].read_text(encoding="utf-8"))
        require(rows and all(not (20.0 <= float(r["sol"]) <= 55.0) for r in rows), "protected synthetic row survived adapter")
        require(all(int(r["iau"]) == 0 and r["complex_key"] == "HIDDEN" for r in rows), "adapter hidden sentinels changed")

    pre1 = a.work / "pre1"
    pre2 = a.work / "pre2"
    for dest in (pre1, pre2):
        run([
            sys.executable, str(a.generator.resolve()),
            "--canonical-2023", str(canon[2023].resolve()),
            "--canonical-2024", str(canon[2024].resolve()),
            "--output", str(dest.resolve()),
        ])
    p1 = pre1 / "FINAL_DENSITY_SYNC_AMOS_2023_2024_PRETRUTH.json"
    p2 = pre2 / "FINAL_DENSITY_SYNC_AMOS_2023_2024_PRETRUTH.json"
    require(p1.read_bytes() == p2.read_bytes(), "identical synthetic inputs did not produce byte-identical pretruth")
    pre = json.loads(p1.read_text(encoding="utf-8"))
    require(pre["events_by_year"] == {"2023": 80, "2024": 80}, f"unexpected retained synthetic event counts: {pre['events_by_year']}")
    require(pre["source_pins"]["density_sync_git_blob"] == "587a304f451e41b9503272f1783a6c6ebb295000", "density-sync source pin changed")
    require(pre["recurrent_annual_eom_sha256"] == pre["density_sync_parent_annual_sha256"], "density-sync parent annual EOM changed")
    require(float(pre["density_sync_annual_reconstruction_max_abs_error"]) <= 1e-12, "annual EOM reconstruction exceeds frozen tolerance")
    require(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "pretruth is truth-bearing")

    label_paths: dict[int, Path] = {}
    for year in (2023, 2024):
        label_paths[year] = a.work / f"labels_{year}.csv"
        rows = sorted(all_labels[year].items())
        write_csv(label_paths[year], ["event_id", "shower_association"], [[eid, lab] for eid, lab in rows])

    post = a.work / "post"
    run([
        sys.executable, str(a.evaluator.resolve()),
        "--pretruth", str(p1.resolve()),
        "--pretruth-sha256", sha(p1),
        "--labels-2023", str(label_paths[2023].resolve()),
        "--labels-2024", str(label_paths[2024].resolve()),
        "--output", str(post.resolve()),
    ])
    result_path = post / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    require(result["verdict"] in PRIMARY, "invalid primary verdict token")
    require(result["incremental_density_synchrony_verdict"] in INCREMENTAL, "invalid incremental verdict token")
    require(result["pretruth_sha256"] == sha(p1), "evaluator did not bind exact pretruth hash")
    require(result["candidate_generation_recomputed_after_labels"] is False, "candidate recomputation flag changed")
    require(result["final_method_switched_after_labels"] is False, "final method switch flag changed")

    bad = a.work / "labels_2024_missing.csv"
    rows = sorted(all_labels[2024].items())[:-1]
    write_csv(bad, ["event_id", "shower_association"], [[eid, lab] for eid, lab in rows])
    failed = subprocess.run([
        sys.executable, str(a.evaluator.resolve()),
        "--pretruth", str(p1.resolve()),
        "--pretruth-sha256", sha(p1),
        "--labels-2023", str(label_paths[2023].resolve()),
        "--labels-2024", str(bad.resolve()),
        "--output", str((a.work / "badpost").resolve()),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0
    require(failed, "incomplete postfreeze label map did not fail closed")

    audit = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT_V1",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT_V1",
        "synthetic_only": True,
        "pretruth_sha256": sha(p1),
        "result_sha256": sha(result_path),
        "primary_test_verdict_is_reporting_only": result["verdict"],
        "tests": {
            "exact_old_adapter_integrated": True,
            "protected_stage1_row_never_reached_geometry": True,
            "one_shared_three_method_pretruth_completed": True,
            "byte_deterministic_pretruth_rerun": True,
            "recurrent_annual_reconstruction_identity": True,
            "labels_opened_only_after_pretruth": True,
            "postfreeze_evaluator_bound_to_pretruth_hash": True,
            "incomplete_label_map_fails_closed": True,
            "no_final_method_switch": True,
        },
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_FULL_PIPELINE_SYNTHETIC_AUDIT.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
