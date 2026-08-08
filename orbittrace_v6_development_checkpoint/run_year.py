#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import pickle
from pathlib import Path
from typing import Any


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--year", required=True, type=int, choices=(2022, 2023))
    p.add_argument("--v6-source", required=True, type=Path)
    p.add_argument("--base-runner", required=True, type=Path)
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()

    v6 = load_module(args.v6_source, f"orbittrace_v6_development_year_{args.year}")
    old = v6.load_base_runner(args.base_runner)
    require(list(old.YEARS) == [2022, 2023] and int(old.MAX_COMPONENTS_PER_BIN) == 128,
            "frozen base catalogue constants changed")
    support = old.load_support_module(args.support_source_parts)
    candidate, base, scorer = support.load_sources(args)
    scan_by_year, calibration_by_year, _hidden_labels, sources = support.parse_catalogue(base)

    require(set(scan_by_year) == {2022, 2023}, "development scan years changed")
    require(set(calibration_by_year) == {2022, 2023}, "development calibration years changed")
    print(
        f"V6_DEVELOPMENT_YEAR_START year={args.year} scan={len(scan_by_year[args.year])} calibration={len(calibration_by_year[args.year])}",
        flush=True,
    )
    audit, anchors, components = v6.scan_year_v6(
        old,
        args.year,
        scan_by_year[args.year],
        calibration_by_year[args.year],
        candidate,
        base,
        scorer,
        support,
    )
    require(len(audit["supported_bins"]) >= 30, "supported-bin gate failed in checkpoint")
    require(audit["proposal_cap_per_window"] == 512, "proposal cap changed")
    require(audit["max_primary_proposals_per_year"] == 36864, "annual proposal budget changed")

    checkpoint = {
        "classification": "exact v6 development scan_year_v6 checkpoint",
        "year": args.year,
        "blind_exclusion": [float(support.BLIND_LOW), float(support.BLIND_HIGH)],
        "catalogue_sources": sources,
        "truth_used_for_scan": False,
        "target_access": False,
        "audit": audit,
        "anchors": anchors,
        "components": components,
        "v6_source_sha256": hashlib.sha256(args.v6_source.read_bytes()).hexdigest(),
        "base_runner_sha256": hashlib.sha256(args.base_runner.read_bytes()).hexdigest(),
    }
    raw = pickle.dumps(checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(digest + "\n")
    print(
        f"V6_DEVELOPMENT_YEAR_DONE year={args.year} anchors={len(anchors)} components={len(components)} checkpoint_sha256={digest}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
