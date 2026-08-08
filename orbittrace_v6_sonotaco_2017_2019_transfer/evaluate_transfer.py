#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

YEARS = (2017, 2019)
BLIND = [20.0, 55.0]
ARCHIVE_SHA256 = {
    2017: "1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf",
    2019: "d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4",
}
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
V8_SOURCE_COMMIT = "c9d6c44704013ba0c9430100e98a29a56b453304"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--pretruth", required=True, type=Path)
    p.add_argument("--v8-baseline", required=True, type=Path)
    p.add_argument("--v8-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--parser-2019", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2017", required=True, type=Path)
    p.add_argument("--archive-2019", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def recovery_at(per_label: list[dict[str, Any]], k: int) -> int:
    return int(sum(
        bool(row.get("qualified", False))
        and row.get("rank") is not None
        and int(row["rank"]) <= k
        for row in per_label
    ))


def add_recovery_cutoffs(full: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in full.items() if k != "per_label"}
    out["recovered_at_25"] = recovery_at(full["per_label"], 25)
    out["recovered_at_50"] = recovery_at(full["per_label"], 50)
    out["recovered_at_100"] = recovery_at(full["per_label"], 100)
    return out


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    pretruth = json.loads(args.pretruth.read_text())
    pretruth_sha = canonical_sha(pretruth)
    pretruth_sidecar = args.pretruth.with_suffix(args.pretruth.suffix + ".sha256")
    require(pretruth_sidecar.exists() and pretruth_sidecar.read_text().strip() == pretruth_sha, "pretruth SHA mismatch")
    require(pretruth["classification"] == "v6 SonotaCo 2017/2019 architecture-pre-frozen pretruth families", "wrong pretruth classification")
    require(pretruth["years"] == list(YEARS) and pretruth["blind_exclusion"] == BLIND, "pretruth universe changed")
    require(pretruth["truth_accessed"] is False and pretruth["event_level_labels_saved"] is False, "truth entered pretruth stage")
    require(pretruth["target_information_accessed"] is False, "target information entered pretruth stage")
    families = pretruth["primary_families"]
    order = [str(x) for x in pretruth["primary_order"]]
    require(len(order) == len(families) == len(set(order)), "pretruth family/order cardinality changed")
    require(order == [str(f["family_id"]) for f in families], "serialized v6 primary order/family list diverged")
    primary_payload = {
        "years": list(YEARS),
        "corpus": pretruth["corpus"],
        "primary_method": "v3",
        "primary_order": order,
        "primary_families": families,
        "scan_audits": pretruth["scan_audits"],
    }
    require(canonical_sha(primary_payload) == pretruth["primary_ranking_sha256_before_truth"], "primary pretruth ranking hash mismatch")

    v8_baseline = json.loads(args.v8_baseline.read_text())
    require(v8_baseline["verdict"] == "PASS_PROMOTED_V8_SONOTACO_2017_2019_SAME_UNIVERSE_BASELINE", "exact promoted-v8 same-universe baseline unavailable")
    require(v8_baseline["years"] == list(YEARS) and v8_baseline["blind_exclusion"] == BLIND, "v8 baseline universe changed")
    require(v8_baseline["v8_source_commit"] == V8_SOURCE_COMMIT, "v8 baseline source changed")
    require(v8_baseline["archive_sha256"] == {str(y): ARCHIVE_SHA256[y] for y in YEARS}, "v8 baseline archive identity changed")
    require(all(v8_baseline["integrity"].values()), "v8 baseline integrity failed")

    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    archives = {2017: args.archive_2017, 2019: args.archive_2019}
    parsers = {2017: args.parser_2017, 2019: args.parser_2019}
    for year in YEARS:
        require(sha256_file(archives[year]) == ARCHIVE_SHA256[year], f"archive hash changed {year}")

    # Load the exact promoted-v8 evaluator implementation. No local replacement
    # of eligibility, family matching, precision, F1, MRR, or top-100 semantics.
    v8 = load_module(args.v8_runner, "orbittrace_v6_transfer_exact_v8_evaluator")
    v8.YEARS = YEARS
    v8.MONTH_KEYS = tuple()
    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()
    v8.mult.TOP_K = 100
    runtime = v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    _candidate, base, _scorer = support.load_sources(args)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")

    # FIRST TRUTH ACCESS IN THIS PROCESS. Parsers themselves remove 20-55 before
    # reading the shower token; the detector/family/rank payload is already frozen.
    hidden_labels: dict[str, str] = {}
    seen: set[str] = set()
    parser_audits: dict[str, Any] = {}
    for year in YEARS:
        parser = load_module(parsers[year], f"orbittrace_v6_transfer_truth_parser_{year}")
        require(int(parser.YEAR) == year, f"parser year mismatch {year}")
        require(float(parser.BLIND_SOLAR_MIN) == 20.0 and float(parser.BLIND_SOLAR_MAX) == 55.0, f"parser blind changed {year}")
        labeled, sporadic, audit = getattr(parser, f"parse_sonotaco_{year}_events")(archives[year], args.mapping_audit, base)
        require(isinstance(audit.get("gates"), dict) and all(audit["gates"].values()), f"catalogue-v6 parser gates failed {year}")
        require("at_least_30_supported_native_codes" not in audit["gates"], "obsolete fixed4 gate remained fatal")
        for event in labeled:
            event_id = str(event["id"])
            require(event_id.startswith(f"{year}:"), f"deterministic year-prefix ID missing {event_id}")
            require(event_id not in seen, f"duplicate event ID {event_id}")
            seen.add(event_id)
            label = str(event.get("complex_key", "")).strip()
            require(label and label != "SPORADIC", f"mapped label missing {event_id}")
            hidden_labels[event_id] = label
        for event in sporadic:
            event_id = str(event["id"])
            require(event_id.startswith(f"{year}:"), f"deterministic year-prefix ID missing {event_id}")
            require(event_id not in seen, f"duplicate event ID {event_id}")
            seen.add(event_id)
            hidden_labels[event_id] = "SPORADIC"
        parser_audits[str(year)] = {
            "gates": dict(audit["gates"]),
            "fixed4_supported_native_code_gate_report_only": bool(audit["fixed4_supported_native_code_gate_report_only"]),
            "counts": dict(audit["counts"]),
            "native_syntax_fraction": float(audit["native_syntax_fraction"]),
            "mapped_nonbackground_fraction": float(audit["mapped_nonbackground_fraction"]),
        }

    family_event_ids = {str(eid) for family in families for eid in family["event_ids"]}
    require(family_event_ids <= set(hidden_labels), "v6 pretruth family contains event outside reloaded common truth")

    v6_full = v8.mult.evaluate_order(hidden_labels, families, order)
    v6_metrics = add_recovery_cutoffs(v6_full)
    v8_metrics = dict(v8_baseline["metrics"])
    for key in ("qualified_matches", "recovered_at_25", "recovered_at_50", "recovered_at_100", "mrr", "macro_f1", "top100_dominant_precision"):
        require(key in v8_metrics, f"v8 baseline missing {key}")
    require(int(v6_metrics["eligible_labels"]) == int(v8_metrics["eligible_labels"]), "v6/v8 same-universe eligible label count differs")

    recovery_floor = math.floor(0.80 * int(v8_metrics["recovered_at_100"]))
    qualified_floor = math.floor(0.60 * int(v8_metrics["qualified_matches"]))
    mrr_floor = 0.80 * float(v8_metrics["mrr"])
    strict_improvements = {
        "recovery_at_25": int(v6_metrics["recovered_at_25"]) > int(v8_metrics["recovered_at_25"]),
        "recovery_at_50": int(v6_metrics["recovered_at_50"]) > int(v8_metrics["recovered_at_50"]),
        "recovery_at_100": int(v6_metrics["recovered_at_100"]) > int(v8_metrics["recovered_at_100"]),
        "mrr": float(v6_metrics["mrr"]) > float(v8_metrics["mrr"]),
        "macro_f1": float(v6_metrics["macro_f1"]) > float(v8_metrics["macro_f1"]),
    }
    integrity_gates = {
        "pretruth_hash_verified": len(pretruth_sha) == 64,
        "pretruth_truth_access_false": pretruth["truth_accessed"] is False,
        "pretruth_event_labels_not_saved": pretruth["event_level_labels_saved"] is False,
        "pretruth_target_access_false": pretruth["target_information_accessed"] is False,
        "all_year_scan_supported_bins_at_least_30": all(len(a["supported_bins"]) >= 30 for a in pretruth["scan_audits"]),
        "all_year_proposal_caps_exact_512": all(a["proposal_cap_per_window"] == 512 for a in pretruth["scan_audits"]),
        "all_year_annual_primary_budget_exact_36864": all(a["max_primary_proposals_per_year"] == 36864 for a in pretruth["scan_audits"]),
        "all_parser_catalogue_v6_gates_pass": all(all(parser_audits[str(y)]["gates"].values()) for y in YEARS),
        "same_exact_archive_identities_as_v8": v8_baseline["archive_sha256"] == {str(y): ARCHIVE_SHA256[y] for y in YEARS},
        "same_eligible_label_universe_as_v8": int(v6_metrics["eligible_labels"]) == int(v8_metrics["eligible_labels"]),
        "exact_promoted_v8_evaluator_used": True,
        "no_parameter_or_threshold_search": True,
        "target_information_accessed": False,
    }
    scientific_gates = {
        "at_least_40_recurrent_v3_primary_families": len(families) >= 40,
        "recovery_at_100_at_least_floor_080_v8": int(v6_metrics["recovered_at_100"]) >= recovery_floor,
        "qualified_matches_at_least_floor_060_v8": int(v6_metrics["qualified_matches"]) >= qualified_floor,
        "top100_dominant_precision_at_least_050": float(v6_metrics["top100_dominant_precision"]) >= 0.50,
        "mrr_at_least_080_v8": float(v6_metrics["mrr"]) >= mrr_floor,
        "at_least_one_frozen_endpoint_strictly_exceeds_v8": any(strict_improvements.values()),
    }
    verdict = (
        "PASS_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER"
        if all(integrity_gates.values()) and all(scientific_gates.values())
        else "FAIL_V6_SONOTACO_2017_2019_ARCHITECTURE_PREFROZEN_TRANSFER"
    )
    result = {
        "verdict": verdict,
        "classification": "architecture-pre-frozen no-retuning SonotaCo 2017/2019 transfer; not pristine prospective validation",
        "years": list(YEARS),
        "blind_exclusion": BLIND,
        "pretruth_sha256": pretruth_sha,
        "primary_ranking_sha256_before_truth": pretruth["primary_ranking_sha256_before_truth"],
        "v6_family_count": len(families),
        "v6": v6_metrics,
        "v8_same_universe": v8_metrics,
        "frozen_retention_thresholds": {
            "recovery_at_100_floor": recovery_floor,
            "qualified_matches_floor": qualified_floor,
            "top100_dominant_precision_floor": 0.50,
            "mrr_floor": mrr_floor,
        },
        "strict_improvements_v6_over_v8": strict_improvements,
        "integrity_gates": integrity_gates,
        "scientific_gates": scientific_gates,
        "parser_audits": parser_audits,
        "claim_boundary": "Architecture-pre-frozen no-retuning generalization evidence only; raw pair is not pristine and this result alone does not authorize an OrbitTrace target-containing run.",
        "target_information_accessed": False,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(canonical_sha(result) + "\n")
    print("ORBITTRACE_V6_TRANSFER_RESULT_BEGIN")
    print(json.dumps({
        "verdict": verdict,
        "v6_family_count": len(families),
        "v6": v6_metrics,
        "v8_same_universe": v8_metrics,
        "scientific_gates": scientific_gates,
    }, indent=2, sort_keys=True))
    print("ORBITTRACE_V6_TRANSFER_RESULT_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
