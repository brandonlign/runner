#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import pickle
import sys
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


def ordered_ids_sha(events: list[dict[str, Any]]) -> str:
    h = hashlib.sha256()
    for event in events:
        h.update(str(event["id"]).encode())
        h.update(b"\0")
    return h.hexdigest()


def load_checkpoint(path: Path, year: int, v6_sha: str, base_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    require(sidecar.exists() and sidecar.read_text().strip() == hashlib.sha256(raw).hexdigest(),
            f"checkpoint byte hash mismatch {year}")
    checkpoint = pickle.loads(raw)
    require(checkpoint["classification"] == "exact v6 development scan_year_v6 checkpoint", "wrong checkpoint classification")
    require(int(checkpoint["year"]) == year, f"checkpoint year mismatch {year}")
    require(checkpoint["blind_exclusion"] == [20.0, 55.0], f"checkpoint blind interval changed {year}")
    require(checkpoint["truth_used_for_scan"] is False and checkpoint["target_access"] is False,
            f"checkpoint firewall failed {year}")
    require(checkpoint["v6_source_sha256"] == v6_sha, f"v6 source mismatch {year}")
    require(checkpoint["base_runner_sha256"] == base_sha, f"base source mismatch {year}")
    require(len(checkpoint["audit"]["supported_bins"]) >= 30, f"supported bins failed {year}")
    require(checkpoint["audit"]["proposal_cap_per_window"] == 512, f"proposal cap changed {year}")
    require(checkpoint["audit"]["max_primary_proposals_per_year"] == 36864, f"annual budget changed {year}")
    return checkpoint


def main() -> int:
    wrapper = argparse.ArgumentParser(add_help=False)
    wrapper.add_argument("--v6-source", required=True, type=Path)
    wrapper.add_argument("--base-runner", required=True, type=Path)
    wrapper.add_argument("--support-source-parts", required=True, type=Path)
    wrapper.add_argument("--checkpoint-2022", required=True, type=Path)
    wrapper.add_argument("--checkpoint-2023", required=True, type=Path)
    wrapper_args, frozen_main_args = wrapper.parse_known_args()

    # The remaining CLI is passed unchanged to the frozen v6 main(), including
    # its candidate/baseline/scorer/fixed4-baseline/output arguments.
    require(frozen_main_args, "missing frozen main arguments")
    v6_sha = hashlib.sha256(wrapper_args.v6_source.read_bytes()).hexdigest()
    base_sha = hashlib.sha256(wrapper_args.base_runner.read_bytes()).hexdigest()
    checkpoints = {
        2022: load_checkpoint(wrapper_args.checkpoint_2022, 2022, v6_sha, base_sha),
        2023: load_checkpoint(wrapper_args.checkpoint_2023, 2023, v6_sha, base_sha),
    }

    v6 = load_module(wrapper_args.v6_source, "orbittrace_v6_development_replay")
    old = v6.load_base_runner(wrapper_args.base_runner)
    support = old.load_support_module(wrapper_args.support_source_parts)
    original_parse_catalogue = support.parse_catalogue

    def verified_parse_catalogue(base: Any):
        scan_by_year, calibration_by_year, hidden_labels, sources = original_parse_catalogue(base)
        require(set(scan_by_year) == {2022, 2023}, "replay scan years changed")
        require(set(calibration_by_year) == {2022, 2023}, "replay calibration years changed")
        for year in (2022, 2023):
            checkpoint = checkpoints[year]
            require(sources == checkpoint["catalogue_sources"], f"catalogue source identity changed {year}")
            require(len(scan_by_year[year]) == checkpoint["scan_count"], f"scan count changed {year}")
            require(len(calibration_by_year[year]) == checkpoint["calibration_count"], f"calibration count changed {year}")
            require(ordered_ids_sha(scan_by_year[year]) == checkpoint["ordered_scan_ids_sha256"],
                    f"ordered scan universe changed {year}")
            require(ordered_ids_sha(calibration_by_year[year]) == checkpoint["ordered_calibration_ids_sha256"],
                    f"ordered calibration universe changed {year}")
        print("PASS_V6_REPLAY_INPUT_IDENTITY_GUARDS", flush=True)
        return scan_by_year, calibration_by_year, hidden_labels, sources

    def replay_scan_year_v6(
        _old: Any,
        year: int,
        events: list[dict[str, Any]],
        calibration_events: list[dict[str, Any]],
        _candidate: Any,
        _base: Any,
        _scorer: Any,
        _support: Any,
    ):
        checkpoint = checkpoints[int(year)]
        require(len(events) == checkpoint["scan_count"], f"replay scan count mismatch {year}")
        require(len(calibration_events) == checkpoint["calibration_count"], f"replay calibration count mismatch {year}")
        require(ordered_ids_sha(events) == checkpoint["ordered_scan_ids_sha256"], f"replay scan order mismatch {year}")
        require(ordered_ids_sha(calibration_events) == checkpoint["ordered_calibration_ids_sha256"],
                f"replay calibration order mismatch {year}")
        print(
            f"V6_DEVELOPMENT_REPLAY year={year} anchors={len(checkpoint['anchors'])} components={len(checkpoint['components'])}",
            flush=True,
        )
        return checkpoint["audit"], checkpoint["anchors"], checkpoint["components"]

    # Reuse the exact module instances and parser in the unchanged frozen main.
    v6.load_base_runner = lambda _path: old
    old.load_support_module = lambda _path: support
    support.parse_catalogue = verified_parse_catalogue
    v6.scan_year_v6 = replay_scan_year_v6

    # Reconstruct the exact CLI expected by the frozen main.  These wrapper-only
    # arguments are reinserted because frozen main needs their paths.
    sys.argv = [str(wrapper_args.v6_source)] + [
        "--base-runner", str(wrapper_args.base_runner),
        "--support-source-parts", str(wrapper_args.support_source_parts),
    ] + frozen_main_args
    print("V6_DEVELOPMENT_REPLAY_MAIN_START", flush=True)
    result = v6.main()
    print("V6_DEVELOPMENT_REPLAY_MAIN_DONE", flush=True)
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
