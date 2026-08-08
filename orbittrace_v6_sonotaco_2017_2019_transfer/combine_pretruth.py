#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

YEARS = (2017, 2019)
CORPUS = "sonotaco-2017-2019-v6-architecture-prefrozen-transfer"
BLIND = [20.0, 55.0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def configure(v6: Any, old: Any, support: Any) -> None:
    require(int(old.MAX_COMPONENTS_PER_BIN) == 128, "MAX_COMPONENTS_PER_BIN changed")
    require(int(old.CALIBRATION_PER_BIN) == 128, "CALIBRATION_PER_BIN changed")
    require(float(old.WINDOW_WIDTH_DEG) == 10.0 and float(old.WINDOW_STEP_DEG) == 5.0, "window geometry changed")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")
    v6.YEARS = YEARS
    old.YEARS = list(YEARS)
    support.YEARS = list(YEARS)
    old.CORPUS = CORPUS
    support.CORPUS = CORPUS


def load_checkpoint(path: Path, year: int) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip() == hashlib.sha256(raw).hexdigest(), f"checkpoint SHA mismatch {year}")
    c = pickle.loads(raw)
    require(c["classification"] == "v6 SonotaCo 2017/2019 architecture-pre-frozen pretruth year checkpoint", "wrong checkpoint class")
    require(int(c["year"]) == year and c["years"] == list(YEARS), "checkpoint year universe changed")
    require(c["blind_exclusion"] == BLIND, "checkpoint blind interval changed")
    require(c["truth_accessed_by_detector"] is False and c["event_level_labels_saved"] is False, "truth entered pretruth checkpoint")
    require(c["target_information_accessed"] is False, "target information entered checkpoint")
    require(len(c["audit"]["supported_bins"]) >= 30, "v6 supported-bin transfer gate failed")
    require(c["audit"]["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(c["audit"]["max_primary_proposals_per_year"] == 36864, "annual proposal budget changed")
    require(all(c["parser"]["catalogue_v6_gates"].values()), "parser transport gate failed")
    return c


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repaired-v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--checkpoint-2017", required=True, type=Path)
    p.add_argument("--checkpoint-2019", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    checkpoints = {year: load_checkpoint(getattr(args, f"checkpoint_{year}"), year) for year in YEARS}
    v6 = load_module(args.repaired_v6_source, "orbittrace_v6_transfer_combine")
    old = load_module(args.base_runner, "orbittrace_v6_transfer_combine_base")
    support = old.load_support_module(args.support_source_parts)
    _candidate, base, _scorer = support.load_sources(args)
    configure(v6, old, support)

    all_anchors = [a for year in YEARS for a in checkpoints[year]["anchors"]]
    all_components = [c for year in YEARS for c in checkpoints[year]["components"]]
    audits = [checkpoints[year]["audit"] for year in YEARS]
    primary_families = v6.build_family_track_v6(old, all_components, base, "v3")
    rescue_families = v6.build_family_track_v6(old, all_components, base, "fixed4_rescue")
    primary_order = [str(f["family_id"]) for f in primary_families]
    require(len(primary_order) == len(set(primary_order)), "primary family IDs not unique")
    primary_payload = {
        "years": list(YEARS),
        "corpus": CORPUS,
        "primary_method": "v3",
        "primary_order": primary_order,
        "primary_families": primary_families,
        "scan_audits": audits,
    }
    primary_sha = canonical_sha(primary_payload)
    out = {
        "classification": "v6 SonotaCo 2017/2019 architecture-pre-frozen pretruth families",
        "years": list(YEARS),
        "blind_exclusion": BLIND,
        "corpus": CORPUS,
        "primary_order": primary_order,
        "primary_families": primary_families,
        "rescue_families": rescue_families,
        "primary_ranking_sha256_before_truth": primary_sha,
        "anchor_count": len(all_anchors),
        "component_count": len(all_components),
        "scan_audits": audits,
        "year_checkpoint_sha256": {str(year): hashlib.sha256(getattr(args, f"checkpoint_{year}").read_bytes()).hexdigest() for year in YEARS},
        "parser_gate_summaries": {str(year): checkpoints[year]["parser"] for year in YEARS},
        "truth_accessed": False,
        "event_level_labels_saved": False,
        "target_information_accessed": False,
    }
    require(primary_sha and len(primary_sha) == 64, "missing pretruth family hash")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    digest = canonical_sha(out)
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print(f"PASS_V6_TRANSFER_PRETRUTH_COMBINE families={len(primary_families)} rescue={len(rescue_families)} primary_sha={primary_sha} pretruth_sha={digest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
