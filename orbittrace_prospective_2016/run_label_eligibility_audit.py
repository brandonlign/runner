#!/usr/bin/env python3
"""Prospective SonotaCo-2016 label/episode eligibility audit with detector scoring prohibited."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import types
from pathlib import Path

import numpy as np

YEAR = 2016
CORPUS = "sonotaco-2016-prospective"
ARCHIVE_SHA256 = "f1fc4586d3efe71b9dc419261c9ad252c5d4f12e80439e94b56c86445520e530"
MEMBER_SHA256 = "6035614d6aa663f0ab0ed63e8e93f439d6e3969307085fc872eb2aaeff79be1f"
EXPECTED_ROWS = 22943
BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
SCORER_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"

# Eligibility gates frozen before any 2016 label value is read.
MIN_SUPPORTED_BINS = 24
MIN_ELIGIBLE_SHOWERS = 20
CALIBRATION_NEGATIVES_PER_BIN = 128
TEST_NEGATIVES_PER_BIN = 64
EXPECTED_K = (4, 6, 8, 12)
N_FOLDS = 5


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--audit", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-source", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def decode_file(path: Path) -> bytes:
    encoded = "".join(path.read_text(encoding="ascii").split())
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def decode_parts(path: Path) -> bytes:
    names = ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]
    parts = [path / name for name in names]
    if not all(part.exists() for part in parts):
        raise RuntimeError("missing frozen scorer parts")
    encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in parts)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def load_module(name: str, source: bytes, expected_hash: str) -> types.ModuleType:
    digest = sha256_bytes(source)
    if digest != expected_hash:
        raise RuntimeError(f"{name} source mismatch: {digest}")
    module = types.ModuleType(name)
    module.__file__ = f"{name}.py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def load_parser(path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("sonotaco_2016_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load prospective parser")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if sha256_bytes(args.archive.read_bytes()) != ARCHIVE_SHA256:
        raise RuntimeError("2016 archive hash changed after structure freeze")

    base = load_module("eligibility_base", decode_file(args.baseline_payload), BASELINE_SOURCE_SHA256)
    scorer = load_module("eligibility_scorer", decode_parts(args.scorer_parts), SCORER_SOURCE_SHA256)
    parser = load_parser(args.parser_source)

    if getattr(parser, "YEAR", None) != YEAR:
        raise RuntimeError("parser year mismatch")
    if getattr(parser, "ARCHIVE_SHA256", None) != ARCHIVE_SHA256:
        raise RuntimeError("parser archive hash mismatch")
    if getattr(parser, "MEMBER_SHA256", None) != MEMBER_SHA256:
        raise RuntimeError("parser member hash mismatch")
    if getattr(parser, "EXPECTED_ROWS", None) != EXPECTED_ROWS:
        raise RuntimeError("parser expected-row mismatch")

    labeled, sporadic, parser_audit = parser.parse_sonotaco_2016_events(args.archive, args.audit, base)
    if not all(bool(value) for value in parser_audit["gates"].values()):
        raise RuntimeError(f"parser gates failed: {parser_audit['gates']}")

    # The inherited parser must have applied the project blind interval before label normalization/storage.
    combined = labeled + sporadic
    blind_violations = [event for event in combined if 20.0 <= float(event["sol"]) <= 55.0]
    if blind_violations:
        raise RuntimeError(f"blind-interval events survived parser: {len(blind_violations)}")

    mondrian = scorer.MondrianWindowFactory(base, sporadic)
    supported_bins: list[int] = []
    for bin_index in range(36):
        try:
            episode = mondrian.make(
                YEAR,
                bin_index,
                scorer.stable_seed("v8-2016-prospective-eligibility-support", CORPUS, YEAR, bin_index),
            )
        except RuntimeError:
            continue
        if len(episode.sun_lon) != 128:
            raise RuntimeError(f"unexpected Mondrian episode size in bin {bin_index}")
        supported_bins.append(bin_index)

    positive_factory = base.EpisodeFactory(labeled, sporadic)
    fold_mapping, fold_units = base.assign_folds(labeled)
    eligible_showers = sorted(positive_factory.shower_years)

    positive_counts_by_k = {str(k): 0 for k in EXPECTED_K}
    positive_fold_counts = {str(fold): 0 for fold in range(N_FOLDS)}
    positive_episode_count = 0
    positive_construction_failures: list[dict[str, object]] = []
    for shower in eligible_showers:
        complex_key = positive_factory.shower_complex[shower]
        fold = int(fold_mapping[complex_key])
        for year in positive_factory.shower_years[shower]:
            if int(year) != YEAR:
                raise RuntimeError(f"unexpected prospective year in positive factory: {year}")
            for k in EXPECTED_K:
                try:
                    episode = scorer.make_positive(
                        base,
                        positive_factory,
                        shower,
                        year,
                        k,
                        scorer.stable_seed("v8-2016-prospective-eligibility-positive", CORPUS, shower, year, k, 0),
                    )
                except Exception as exc:  # eligibility records failure rather than score-shopping around it
                    positive_construction_failures.append({"shower": int(shower), "k": int(k), "error": type(exc).__name__})
                    continue
                if len(episode.sun_lon) != 128:
                    raise RuntimeError("positive episode size changed")
                positive_episode_count += 1
                positive_counts_by_k[str(k)] += 1
                positive_fold_counts[str(fold)] += 1

    calibration_episode_count = len(supported_bins) * CALIBRATION_NEGATIVES_PER_BIN
    heldout_negative_episode_count = len(supported_bins) * TEST_NEGATIVES_PER_BIN

    gates = {
        "structure_hashes_exact": True,
        "parser_all_pass": all(bool(value) for value in parser_audit["gates"].values()),
        "blind_interval_removed": len(blind_violations) == 0,
        "supported_bins_at_least_24": len(supported_bins) >= MIN_SUPPORTED_BINS,
        "eligible_showers_at_least_20": len(eligible_showers) >= MIN_ELIGIBLE_SHOWERS,
        "all_k_represented": all(positive_counts_by_k[str(k)] > 0 for k in EXPECTED_K),
        "all_folds_represented": all(positive_fold_counts[str(fold)] > 0 for fold in range(N_FOLDS)),
        "positive_episodes_construct": positive_episode_count > 0,
        "calibration_count_formula_exact": calibration_episode_count == len(supported_bins) * 128,
        "negative_count_formula_exact": heldout_negative_episode_count == len(supported_bins) * 64,
        "benchmark_episode_size_128": int(getattr(scorer, "EPISODE_SIZE", 128)) == 128,
    }
    verdict = "PASS_SONOTACO_2016_LABEL_ELIGIBILITY_AUDIT" if all(gates.values()) else "FAIL_SONOTACO_2016_LABEL_ELIGIBILITY_AUDIT"
    result = {
        "verdict": verdict,
        "classification": "prospective eligibility audit only; detector component scores and all scientific endpoints prohibited",
        "year": YEAR,
        "transport_freeze": {
            "archive_sha256": ARCHIVE_SHA256,
            "member_sha256": MEMBER_SHA256,
            "expected_rows": EXPECTED_ROWS,
        },
        "parser_audit": parser_audit,
        "eligibility": {
            "labeled_events_after_filters_and_blind_exclusion": len(labeled),
            "sporadic_events_after_filters_and_blind_exclusion": len(sporadic),
            "supported_bins": supported_bins,
            "supported_bin_count": len(supported_bins),
            "eligible_shower_count": len(eligible_showers),
            "eligible_shower_ids_sha256": hashlib.sha256(json.dumps(eligible_showers, separators=(",", ":")).encode()).hexdigest(),
            "fold_unit_count": len(fold_units),
            "positive_counts_by_k_one_probe_per_shower_year": positive_counts_by_k,
            "positive_fold_counts_one_probe_per_k": positive_fold_counts,
            "positive_episode_count_one_probe_per_k": positive_episode_count,
            "positive_construction_failures": positive_construction_failures,
            "calibration_episode_count_planned": calibration_episode_count,
            "heldout_negative_episode_count_planned": heldout_negative_episode_count,
        },
        "gates": gates,
        "prohibited_endpoints": {
            "v3_scores_computed": False,
            "fixed4_scores_computed": False,
            "v8_statistics_computed": False,
            "component_pvalues_computed": False,
            "auroc_computed": False,
            "recall_computed": False,
            "fpr_computed": False,
        },
    }
    (args.output / "SONOTACO_2016_LABEL_ELIGIBILITY_RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
