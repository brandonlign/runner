#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

P13_ZIP_SHA256 = "efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a"
V8_ZIP_SHA256 = "88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e"
P13_CORE_SHA256 = "12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c"
P13_HALO_SHA256 = "f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--p13-dir", required=True, type=Path)
    p.add_argument("--v8-dir", required=True, type=Path)
    p.add_argument("--p13-zip", required=True, type=Path)
    p.add_argument("--v8-zip", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    require(sha(a.p13_zip) == P13_ZIP_SHA256, "P14 P13 artifact ZIP identity changed")
    require(sha(a.v8_zip) == V8_ZIP_SHA256, "P14 v8 artifact ZIP identity changed")
    p13 = json.loads((a.p13_dir / "dual_output_core_halo_p13_development.json").read_text())
    core = json.loads((a.p13_dir / "p13_core_pretruth.json").read_text())
    v8 = json.loads((a.v8_dir / "pooled_year_centroid_v8_development.json").read_text())

    require(p13["verdict"] == "PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT", "P14 prerequisite P13 not PASS")
    require(p13["target_information_access"] is False and p13["no_new_truth_query"] is True, "P14 P13 firewall changed")
    require(p13["configuration"]["blind_exclusion"] == [20.0, 55.0], "P14 P13 blind interval changed")
    require(len(core) == 226 and len({str(x["family_id"]) for x in core}) == 226, "P14 core universe changed")
    require(canonical_sha(core) == P13_CORE_SHA256, "P14 P13 core order/hash changed")
    require(str(p13["halo_pretruth_sha256"]) == P13_HALO_SHA256, "P14 P13 halo hash changed")

    fs = v8["family_scoring_summary"]
    require(int(v8["family_count"]) == 226, "P14 v8 family count changed")
    require(int(fs["families_requested"]) == 226, "P14 v8 requested family count changed")
    require(int(fs["families_scored"]) == 226, "P14 fallback would be nonvacuous on development")
    require(int(fs["episode_count"]) == 452, "P14 v8 development episode count changed")
    require(fs["episode_sizes"] == [128], "P14 v8 development episode size changed")

    core_metrics = p13["core_discovery"]
    require(core_metrics == {
        "qualified_matches": 95,
        "recovered_at_100": 58,
        "recovered_at_500": 95,
        "mrr": 0.045531138942766655,
        "top100_dominant_precision": 0.6884631112636006,
    }, "P14 P13 core endpoints changed")
    halo = p13["halo_membership"]
    require(abs(float(halo["macro_f1"]) - 0.37661279333940806) < 1e-15, "P14 halo macro F1 changed")
    require(abs(float(halo["large_shower"]["mean_recall"]) - 0.24179462579908398) < 1e-15, "P14 halo recall changed")
    require(abs(float(halo["large_shower"]["mean_precision"]) - 0.8778478363509471) < 1e-15, "P14 halo precision changed")

    result = {
        "verdict": "PASS_SUPPORT_SAFE_MULTIPLICITY_RANK_P14_DEVELOPMENT",
        "classification": "P13 dual-output core/halo plus fail-closed multiplicity rank completion only when exact 128-event scoring is undefined",
        "configuration": {
            "years": [2022, 2023],
            "blind_exclusion": [20.0, 55.0],
            "episode_size": 128,
            "development_family_count": 226,
            "support_safe_fallback_used_on_development": False,
            "unscorable_rank_rule": "after all exact-v8-scored families; lexicographic stable family_id",
            "fabricated_scores": False,
            "episode_size_relaxed": False,
            "parameter_search": False,
            "detector_recomputed": False,
        },
        "core_discovery": core_metrics,
        "halo_membership": halo,
        "gates": {
            "authoritative_p13_pass": True,
            "all_226_development_families_exactly_v8_scorable": True,
            "all_452_development_episodes_exactly_128": True,
            "support_safe_fallback_vacuous_on_development": True,
            "p13_core_order_hash_exact": True,
            "p13_halo_hash_exact": True,
            "p13_core_endpoints_exact": True,
            "no_detector_recomputation": True,
            "no_new_truth_query": True,
            "target_firewall_preserved": True,
        },
        "core_pretruth_sha256": P13_CORE_SHA256,
        "halo_pretruth_sha256": P13_HALO_SHA256,
        "p13_artifact_zip_sha256": P13_ZIP_SHA256,
        "v8_artifact_zip_sha256": V8_ZIP_SHA256,
        "target_information_access": False,
        "no_new_truth_query": True,
    }
    (a.output / "support_safe_multiplicity_rank_p14_development.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (a.output / "SUPPORT_SAFE_MULTIPLICITY_RANK_P14_DEVELOPMENT.md").write_text(
        "# OrbitTrace P14 support-safe multiplicity rank completion\n\n"
        "**PASS** — development compatibility is exact.\n\n"
        "- 226/226 recurrent families were already multiplicity-scorable.\n"
        "- 452/452 frozen development episodes were exactly 128 events.\n"
        "- P14 fallback is therefore vacuous on development.\n"
        "- P13 core order/hash/endpoints and exact P12 halo are unchanged.\n"
        "- No detector or truth recomputation occurred.\n"
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
