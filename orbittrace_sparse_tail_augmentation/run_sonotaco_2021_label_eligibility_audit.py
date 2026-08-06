#!/usr/bin/env python3
"""Audit the frozen SonotaCo-2021 episode universe without computing detector scores."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import sys
import types
from pathlib import Path
from typing import Any

BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
SCORER_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
YEAR = 2021
CORPUS = "sonotaco-2021-sparse-tail-validation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--confirmation-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def decode_file(path: Path) -> bytes:
    encoded = "".join(path.read_text(encoding="ascii").split())
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def decode_parts(path: Path, expected: list[str]) -> bytes:
    parts = sorted(path.glob("part*.b64"))
    if [part.name for part in parts] != expected:
        raise RuntimeError(f"unexpected source parts: {[part.name for part in parts]}")
    encoded = "".join("".join(part.read_text(encoding="ascii").split()) for part in parts)
    return gzip.decompress(base64.b64decode(encoded, validate=True))


def load_module(name: str, source: bytes, expected_hash: str | None = None) -> types.ModuleType:
    digest = sha256_bytes(source)
    if expected_hash is not None and digest != expected_hash:
        raise RuntimeError(f"{name} source mismatch: {digest}")
    module = types.ModuleType(name)
    module.__file__ = f"{name}.py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    base = load_module(
        "sonotaco_2021_eligibility_base",
        decode_file(args.baseline_payload),
        BASELINE_SOURCE_SHA256,
    )
    scorer = load_module(
        "sonotaco_2021_eligibility_scorer",
        decode_parts(args.scorer_parts, ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]),
        SCORER_SOURCE_SHA256,
    )
    confirmation_payload = args.confirmation_source.read_bytes()
    confirmation = load_module("sonotaco_2021_confirmation", confirmation_payload)
    parser = getattr(confirmation, "parse_sonotaco_2021_events")
    labeled, sporadic, parser_audit = parser(args.archive, args.audit, base)

    mondrian = scorer.MondrianWindowFactory(base, sporadic)
    supported_bins: list[int] = []
    for bin_index in range(36):
        try:
            mondrian.make(
                YEAR,
                bin_index,
                scorer.stable_seed("fixed4-confirmation-support", CORPUS, YEAR, bin_index),
            )
        except RuntimeError:
            continue
        supported_bins.append(bin_index)

    positive_factory = base.EpisodeFactory(labeled, sporadic)
    fold_mapping, fold_units = base.assign_folds(labeled)
    eligible_showers = sorted(positive_factory.shower_years)
    shower_year_pairs = sum(len(positive_factory.shower_years[shower]) for shower in eligible_showers)
    positive_episode_count = shower_year_pairs * len(scorer.ALL_K) * scorer.POSITIVE_REPLICATES
    calibration_episode_count = len(supported_bins) * scorer.CALIBRATION_NEGATIVES_PER_BIN
    negative_episode_count = len(supported_bins) * scorer.TEST_NEGATIVES_PER_BIN
    fold_unit_counts = {str(fold): len(fold_units[fold]) for fold in range(base.N_FOLDS)}
    positive_counts_by_fold = {str(fold): 0 for fold in range(base.N_FOLDS)}
    for shower in eligible_showers:
        fold = int(fold_mapping[positive_factory.shower_complex[shower]])
        positive_counts_by_fold[str(fold)] += (
            len(positive_factory.shower_years[shower])
            * len(scorer.ALL_K)
            * scorer.POSITIVE_REPLICATES
        )

    gates = {
        "parser_all_pass": all(bool(value) for value in parser_audit["gates"].values()),
        "at_least_30_supported_bins": len(supported_bins) >= 30,
        "at_least_30_eligible_showers": len(eligible_showers) >= 30,
        "all_five_folds_nonempty": all(count > 0 for count in fold_unit_counts.values()),
        "all_five_folds_have_positive_episodes": all(
            count > 0 for count in positive_counts_by_fold.values()
        ),
        "calibration_resolution_supports_alpha_001": scorer.CALIBRATION_NEGATIVES_PER_BIN >= 100,
        "no_detector_score_computed": True,
    }
    verdict = (
        "PASS_SONOTACO_2021_LABEL_ELIGIBILITY_AUDIT"
        if all(gates.values())
        else "FAIL_SONOTACO_2021_LABEL_ELIGIBILITY_AUDIT"
    )
    result: dict[str, Any] = {
        "verdict": verdict,
        "classification": (
            "label mapping, episode eligibility, and null-window support audit after sparse-tail "
            "margin freeze; no fixed4, wavelet, or augmented score computed"
        ),
        "year": YEAR,
        "corpus": CORPUS,
        "confirmation_source_sha256": sha256_bytes(confirmation_payload),
        "parser_audit": parser_audit,
        "counts": {
            "labeled_events": len(labeled),
            "sporadic_events": len(sporadic),
            "supported_bins": supported_bins,
            "supported_bin_count": len(supported_bins),
            "eligible_showers": eligible_showers,
            "eligible_shower_count": len(eligible_showers),
            "shower_year_pairs": shower_year_pairs,
            "calibration_episodes": calibration_episode_count,
            "negative_episodes": negative_episode_count,
            "positive_episodes": positive_episode_count,
            "fold_unit_counts": fold_unit_counts,
            "positive_episode_counts_by_fold": positive_counts_by_fold,
        },
        "benchmark_constants": {
            "calibration_per_bin": scorer.CALIBRATION_NEGATIVES_PER_BIN,
            "negative_per_bin": scorer.TEST_NEGATIVES_PER_BIN,
            "positive_replicates": scorer.POSITIVE_REPLICATES,
            "member_counts": list(scorer.ALL_K),
            "folds": base.N_FOLDS,
            "sparse_tail_margin": 0.25,
        },
        "gates": gates,
        "prohibited_access": {
            "fixed4_scores": False,
            "wavelet_coefficients": False,
            "sparse_tail_scores": False,
            "auc_or_recall": False,
        },
    }
    (args.output / "sonotaco_2021_label_eligibility_audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
