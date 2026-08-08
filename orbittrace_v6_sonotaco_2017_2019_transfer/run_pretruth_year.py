#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

from orbittrace_v6_sonotaco_2017_2019_transfer.parallel_exact_rescore import install as install_parallel_exact

YEARS = (2017, 2019)
CORPUS = "sonotaco-2017-2019-v6-architecture-prefrozen-transfer"
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
ARCHIVE_SHA256 = {
    2017: "1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf",
    2019: "d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4",
}
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def configure_transfer(v6: Any, old: Any, support: Any) -> None:
    require(int(old.MAX_COMPONENTS_PER_BIN) == 128, "MAX_COMPONENTS_PER_BIN changed")
    require(int(old.CALIBRATION_PER_BIN) == 128, "CALIBRATION_PER_BIN changed")
    require(float(old.WINDOW_WIDTH_DEG) == 10.0, "WINDOW_WIDTH_DEG changed")
    require(float(old.WINDOW_STEP_DEG) == 5.0, "WINDOW_STEP_DEG changed")
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "blind interval changed")
    v6.YEARS = YEARS
    old.YEARS = list(YEARS)
    support.YEARS = list(YEARS)
    old.CORPUS = CORPUS
    support.CORPUS = CORPUS


def geometry(event: dict[str, Any], year: int) -> dict[str, Any]:
    return {
        "id": str(event["id"]),
        "year": int(year),
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=YEARS)
    p.add_argument("--repaired-v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--parallel-exact-workers", type=int, default=4)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_file(args.archive) == ARCHIVE_SHA256[args.year], f"archive hash changed {args.year}")
    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")

    v6 = load_module(args.repaired_v6_source, f"orbittrace_v6_transfer_{args.year}")
    old = load_module(args.base_runner, f"orbittrace_v6_transfer_base_{args.year}")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    configure_transfer(v6, old, support)

    parser = load_module(args.parser, f"orbittrace_sonotaco_catalogue_parser_{args.year}")
    require(int(parser.YEAR) == args.year, "parser year mismatch")
    require(float(parser.BLIND_SOLAR_MIN) == BLIND_LOW and float(parser.BLIND_SOLAR_MAX) == BLIND_HIGH, "parser blind interval changed")
    fn = getattr(parser, f"parse_sonotaco_{args.year}_events")
    labeled, sporadic, parser_audit = fn(args.archive, args.mapping_audit, base)
    require(isinstance(parser_audit.get("gates"), dict) and all(parser_audit["gates"].values()), "catalogue-v6 parser gates failed")
    require("at_least_30_supported_native_codes" not in parser_audit["gates"], "obsolete fixed4 supported-code gate remained fatal")
    require(parser_audit.get("fixed4_supported_native_code_gate_report_only") in {True, False}, "fixed4 supported-code diagnostic missing")
    require(int(parser_audit["counts"]["sporadic_events"]) >= 10000, "insufficient background events")
    require(int(parser_audit["counts"]["distinct_labeled_showers"]) >= 30, "insufficient mapped showers")
    require(float(parser_audit["native_syntax_fraction"]) >= 0.90, "native syntax gate failed")
    require(float(parser_audit["mapped_nonbackground_fraction"]) >= 0.90, "mapped label fraction gate failed")

    seen: set[str] = set()
    scan_events: list[dict[str, Any]] = []
    for event in labeled + sporadic:
        event_id = str(event["id"])
        require(event_id not in seen, f"duplicate event ID {event_id}")
        seen.add(event_id)
        scan_events.append(geometry(event, args.year))
    calibration_events = [dict(geometry(event, args.year), complex_key="SPORADIC") for event in sporadic]
    scan_events.sort(key=lambda e: (float(e["sol"]), str(e["id"])))
    calibration_events.sort(key=lambda e: (float(e["sol"]), str(e["id"])))
    require(all(not (BLIND_LOW <= float(e["sol"]) <= BLIND_HIGH) for e in scan_events), "target interval entered scan")
    require({str(e["id"]) for e in calibration_events} <= {str(e["id"]) for e in scan_events}, "calibration outside scan")

    execution = {"parallel_exact_enabled": False, "parallel_exact_workers": 0}
    if args.parallel_exact_workers > 0:
        execution.update(install_parallel_exact(v6, workers=args.parallel_exact_workers, min_parallel_records=256))
        execution["parallel_exact_enabled"] = True
        execution["parallel_exact_workers"] = int(execution["workers"])

    audit, anchors, components = v6.scan_year_v6(old, args.year, scan_events, calibration_events, candidate, base, scorer, support)
    require(len(audit["supported_bins"]) >= 30, "fewer than 30 supported v6 calibration bins")
    require(audit["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(audit["max_primary_proposals_per_year"] == 36864, "annual primary budget changed")

    pretruth_parser_summary = {
        "year": args.year,
        "archive_sha256": ARCHIVE_SHA256[args.year],
        "mapping_audit_sha256": MAPPING_AUDIT_SHA256,
        "catalogue_v6_gates": dict(parser_audit["gates"]),
        "fixed4_supported_native_code_gate_report_only": bool(parser_audit["fixed4_supported_native_code_gate_report_only"]),
        "counts": dict(parser_audit["counts"]),
        "native_syntax_fraction": float(parser_audit["native_syntax_fraction"]),
        "mapped_nonbackground_fraction": float(parser_audit["mapped_nonbackground_fraction"]),
        "event_level_labels_saved": False,
        "blind_interval_removed_before_label_access": True,
    }
    checkpoint = {
        "classification": "v6 SonotaCo 2017/2019 architecture-pre-frozen pretruth year checkpoint",
        "year": args.year,
        "years": list(YEARS),
        "corpus": CORPUS,
        "blind_exclusion": [BLIND_LOW, BLIND_HIGH],
        "scan_count": len(scan_events),
        "calibration_count": len(calibration_events),
        "parser": pretruth_parser_summary,
        "execution": execution,
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "truth_accessed_by_detector": False,
        "event_level_labels_saved": False,
        "target_information_accessed": False,
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    path = args.output / f"v6_transfer_{args.year}_pretruth.pkl"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(digest + "\n")
    (args.output / f"v6_transfer_{args.year}_summary.json").write_text(json.dumps({
        "year": args.year,
        "checkpoint_sha256": digest,
        "scan_count": len(scan_events),
        "calibration_count": len(calibration_events),
        "supported_bins": len(audit["supported_bins"]),
        "anchors": len(anchors),
        "components": len(components),
        "parallel_exact_workers": execution["parallel_exact_workers"],
        "fixed4_supported_native_code_gate_report_only": pretruth_parser_summary["fixed4_supported_native_code_gate_report_only"],
    }, indent=2, sort_keys=True) + "\n")
    print(f"PASS_V6_TRANSFER_PRETRUTH_YEAR year={args.year} scan={len(scan_events)} calibration={len(calibration_events)} components={len(components)} sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
