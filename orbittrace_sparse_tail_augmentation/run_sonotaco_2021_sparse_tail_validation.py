#!/usr/bin/env python3
"""Prospective SonotaCo-2021 validation of fixed4, wavelet, and sparse-tail augmentation."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import multiprocessing as mp
import os
import sys
import types
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import roc_auc_score

import sparse_tail_augmentation as sparse_tail
import wavelet_episode_comparator as wavelet

YEAR = 2021
CORPUS = "sonotaco-2021-sparse-tail-validation"
ARCHIVE_SHA256 = "8d58f089c4137e4de3994fedf57d10571a98e6f594535199fe30d5ec5f251efb"
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
CONFIRMATION_SOURCE_SHA256 = "1af6addf880c8041b613fa12fc8c4d588a7140ae8e40fab0e2ceebcd0d566337"
BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
SCORER_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
EXPECTED_SUPPORTED_BINS = (
    0, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
    19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
)
EXPECTED_ELIGIBLE_SHOWERS = (
    1, 2, 4, 5, 7, 8, 10, 11, 12, 13, 15, 16, 17, 19, 20, 22, 23,
    175, 191, 208, 215, 245, 250, 331, 334, 335, 337, 338, 339, 341,
    411, 444, 445, 480, 502, 529, 613,
)
EXPECTED_CALIBRATION_EPISODES = 4224
EXPECTED_NEGATIVE_EPISODES = 2112
EXPECTED_POSITIVE_EPISODES = 592
FIXED4_ID = "orbittrace_fixed4"
WAVELET_ID = "brown2010_wavelet_episode_core"
COMPONENT_METHODS = (FIXED4_ID, WAVELET_ID)
METHODS = COMPONENT_METHODS + (sparse_tail.METHOD_ID,)

_WORKER_BASE: types.ModuleType | None = None
_WORKER_SCORER: types.ModuleType | None = None
_WORKER_CONFIRMATION: types.ModuleType | None = None
_WORKER_MONDRIAN: Any = None
_WORKER_POSITIVE: Any = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--confirmation-source", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--eligibility-freeze", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)))
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


def load_module(name: str, source: bytes, expected_hash: str) -> types.ModuleType:
    digest = sha256_bytes(source)
    if digest != expected_hash:
        raise RuntimeError(f"{name} source mismatch: {digest}")
    module = types.ModuleType(name)
    module.__file__ = f"{name}.py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def load_sources(args: argparse.Namespace) -> tuple[types.ModuleType, types.ModuleType, types.ModuleType]:
    base = load_module(
        "sparse_tail_2021_base",
        decode_file(args.baseline_payload),
        BASELINE_SOURCE_SHA256,
    )
    scorer = load_module(
        "sparse_tail_2021_scorer",
        decode_parts(args.scorer_parts, ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]),
        SCORER_SOURCE_SHA256,
    )
    confirmation = load_module(
        "sparse_tail_2021_confirmation",
        args.confirmation_source.read_bytes(),
        CONFIRMATION_SOURCE_SHA256,
    )
    return base, scorer, confirmation


def validate_freezes(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    eligibility = json.loads(args.eligibility_freeze.read_text(encoding="utf-8"))
    if protocol.get("status") != "frozen_before_any_sonotaco_2021_component_or_sparse_tail_score":
        raise RuntimeError("prospective protocol was not frozen before scoring")
    method = protocol.get("method", {})
    if method.get("id") != sparse_tail.METHOD_ID or float(method.get("margin")) != sparse_tail.MARGIN:
        raise RuntimeError("sparse-tail method freeze mismatch")
    if protocol["prospective_panel"]["year"] != YEAR:
        raise RuntimeError("unexpected prospective validation year")
    if eligibility.get("verdict") != "PASS_SONOTACO_2021_LABEL_ELIGIBILITY_AUDIT":
        raise RuntimeError("2021 eligibility freeze did not pass")
    if eligibility["benchmark_constants"]["sparse_tail_margin"] != sparse_tail.MARGIN:
        raise RuntimeError("eligibility margin mismatch")
    if any(eligibility.get("prohibited_access", {}).values()):
        raise RuntimeError("2021 scores were accessed during eligibility audit")
    counts = eligibility["counts"]
    if tuple(counts["supported_bins"]) != EXPECTED_SUPPORTED_BINS:
        raise RuntimeError("supported-bin freeze mismatch")
    if tuple(counts["eligible_showers"]) != EXPECTED_ELIGIBLE_SHOWERS:
        raise RuntimeError("eligible-shower freeze mismatch")
    if counts["calibration_episodes"] != EXPECTED_CALIBRATION_EPISODES:
        raise RuntimeError("calibration episode freeze mismatch")
    if counts["negative_episodes"] != EXPECTED_NEGATIVE_EPISODES:
        raise RuntimeError("negative episode freeze mismatch")
    if counts["positive_episodes"] != EXPECTED_POSITIVE_EPISODES:
        raise RuntimeError("positive episode freeze mismatch")
    return protocol, eligibility


def score_episode(episode: Any) -> dict[str, float]:
    if _WORKER_BASE is None or _WORKER_SCORER is None or _WORKER_CONFIRMATION is None:
        raise RuntimeError("worker state unavailable")
    fixed4 = float(_WORKER_CONFIRMATION.fixed4_score(_WORKER_BASE, _WORKER_SCORER, episode))
    wavelet_score = float(wavelet.wavelet_episode_score(episode))
    scores = {FIXED4_ID: fixed4, WAVELET_ID: wavelet_score}
    if set(scores) != set(COMPONENT_METHODS) or not all(np.isfinite(value) for value in scores.values()):
        raise RuntimeError(f"invalid component scores: {scores}")
    return scores


def score_background(task: tuple[str, int, int]) -> dict[str, Any]:
    if _WORKER_MONDRIAN is None or _WORKER_SCORER is None:
        raise RuntimeError("worker background factory unavailable")
    kind, bin_index, index = task
    prefix = "fixed4-confirmation-calibration" if kind == "calibration" else "fixed4-confirmation-negative"
    episode = _WORKER_MONDRIAN.make(
        YEAR,
        bin_index,
        _WORKER_SCORER.stable_seed(prefix, CORPUS, YEAR, bin_index, index),
    )
    return {
        "kind": kind,
        "bin": bin_index,
        "index": index,
        "center_sol": float(episode.center_sol),
        "scores": score_episode(episode),
    }


def score_positive(task: tuple[int, int, int, int, int, str]) -> dict[str, Any]:
    if _WORKER_POSITIVE is None or _WORKER_SCORER is None or _WORKER_BASE is None:
        raise RuntimeError("worker positive factory unavailable")
    shower, year, k, replicate, fold, complex_key = task
    episode = _WORKER_SCORER.make_positive(
        _WORKER_BASE,
        _WORKER_POSITIVE,
        shower,
        year,
        k,
        _WORKER_SCORER.stable_seed("fixed4-confirmation-positive", CORPUS, shower, year, k, replicate),
    )
    return {
        "shower": shower,
        "year": year,
        "k": k,
        "replicate": replicate,
        "fold": fold,
        "complex_key": complex_key,
        "bin": int(_WORKER_SCORER.mondrian_bin_of(episode.center_sol)),
        "center_sol": float(episode.center_sol),
        "scores": score_episode(episode),
    }


def auc(positive: Iterable[float], negative: Iterable[float]) -> float:
    pos = list(positive)
    neg = list(negative)
    labels = np.asarray([1] * len(pos) + [0] * len(neg), dtype=np.int8)
    return float(roc_auc_score(labels, np.asarray(pos + neg, dtype=np.float64)))


def rate(values: Iterable[float], alpha: float) -> float:
    array = np.asarray(list(values), dtype=np.float64)
    if not len(array):
        raise ValueError("empty rate input")
    return float(np.mean(array <= alpha))


def main() -> None:
    global _WORKER_BASE, _WORKER_SCORER, _WORKER_CONFIRMATION, _WORKER_MONDRIAN, _WORKER_POSITIVE

    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol, eligibility = validate_freezes(args)
    if sha256_bytes(args.archive.read_bytes()) != ARCHIVE_SHA256:
        raise RuntimeError("2021 archive changed after structure freeze")
    if sha256_bytes(args.audit.read_bytes()) != MAPPING_AUDIT_SHA256:
        raise RuntimeError("mapping audit changed")
    if not all(wavelet.self_test().values()):
        raise RuntimeError("wavelet source self-test failed")
    if not all(sparse_tail.self_test().values()):
        raise RuntimeError("sparse-tail source self-test failed")

    base, scorer, confirmation = load_sources(args)
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

    if tuple(supported_bins) != EXPECTED_SUPPORTED_BINS:
        raise RuntimeError(f"supported bins changed: {supported_bins}")
    if tuple(eligible_showers) != EXPECTED_ELIGIBLE_SHOWERS:
        raise RuntimeError(f"eligible showers changed: {eligible_showers}")

    _WORKER_BASE = base
    _WORKER_SCORER = scorer
    _WORKER_CONFIRMATION = confirmation
    _WORKER_MONDRIAN = mondrian
    _WORKER_POSITIVE = positive_factory

    calibration_tasks = [
        ("calibration", bin_index, index)
        for bin_index in supported_bins
        for index in range(scorer.CALIBRATION_NEGATIVES_PER_BIN)
    ]
    negative_tasks = [
        ("negative", bin_index, index)
        for bin_index in supported_bins
        for index in range(scorer.TEST_NEGATIVES_PER_BIN)
    ]
    positive_tasks = [
        (
            shower,
            year,
            k,
            replicate,
            int(fold_mapping[positive_factory.shower_complex[shower]]),
            str(positive_factory.shower_complex[shower]),
        )
        for shower in eligible_showers
        for year in positive_factory.shower_years[shower]
        for k in scorer.ALL_K
        for replicate in range(scorer.POSITIVE_REPLICATES)
    ]
    if len(calibration_tasks) != EXPECTED_CALIBRATION_EPISODES:
        raise RuntimeError("calibration task count changed")
    if len(negative_tasks) != EXPECTED_NEGATIVE_EPISODES:
        raise RuntimeError("negative task count changed")
    if len(positive_tasks) != EXPECTED_POSITIVE_EPISODES:
        raise RuntimeError("positive task count changed")

    workers = max(1, int(args.workers))
    if workers == 1:
        calibration_rows = [score_background(task) for task in calibration_tasks]
        negative_rows = [score_background(task) for task in negative_tasks]
        positive_rows = [score_positive(task) for task in positive_tasks]
    else:
        with mp.get_context("fork").Pool(processes=workers) as pool:
            calibration_rows = pool.map(score_background, calibration_tasks, chunksize=4)
            negative_rows = pool.map(score_background, negative_tasks, chunksize=4)
            positive_rows = pool.map(score_positive, positive_tasks, chunksize=2)

    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in COMPONENT_METHODS}
    for method in COMPONENT_METHODS:
        for bin_index in supported_bins:
            values = np.asarray(
                [row["scores"][method] for row in calibration_rows if row["bin"] == bin_index],
                dtype=np.float64,
            )
            if len(values) != scorer.CALIBRATION_NEGATIVES_PER_BIN:
                raise RuntimeError(f"calibration mismatch method={method} bin={bin_index}")
            calibration[method][bin_index] = values

    sparse_tail_calibration = {
        bin_index: sparse_tail.calibration_statistics(
            calibration[FIXED4_ID][bin_index],
            calibration[WAVELET_ID][bin_index],
        )
        for bin_index in supported_bins
    }

    for row in negative_rows + positive_rows:
        bin_index = row["bin"]
        row["p"] = {
            method: sparse_tail.target_survival_pvalue(
                row["scores"][method], calibration[method][bin_index]
            )
            for method in COMPONENT_METHODS
        }
        candidate_statistic = sparse_tail.target_statistic(
            row["scores"][FIXED4_ID],
            row["scores"][WAVELET_ID],
            calibration[FIXED4_ID][bin_index],
            calibration[WAVELET_ID][bin_index],
        )
        row["scores"][sparse_tail.METHOD_ID] = candidate_statistic
        row["p"][sparse_tail.METHOD_ID] = sparse_tail.final_pvalue(
            candidate_statistic,
            sparse_tail_calibration[bin_index],
        )
    for row in negative_rows:
        row["reporting_sector"] = int(scorer.reporting_sector_of(row["center_sol"]))

    weak = [row for row in positive_rows if row["k"] in scorer.WEAK_K]
    metrics: dict[str, Any] = {}
    for method in METHODS:
        negative_scores = [row["scores"][method] for row in negative_rows]
        sector_fpr = {
            str(sector): rate(
                (row["p"][method] for row in negative_rows if row["reporting_sector"] == sector),
                0.05,
            )
            for sector in sorted({row["reporting_sector"] for row in negative_rows})
        }
        metrics[method] = {
            "weak_auc": auc((row["scores"][method] for row in weak), negative_scores),
            "fold_auc": {
                str(fold): auc(
                    (row["scores"][method] for row in weak if row["fold"] == fold),
                    negative_scores,
                )
                for fold in range(base.N_FOLDS)
            },
            "fpr": {
                str(alpha): rate((row["p"][method] for row in negative_rows), alpha)
                for alpha in scorer.ALPHAS
            },
            "worst_sector_fpr_005": max(sector_fpr.values()),
            "recall": {
                str(alpha): {
                    str(k): rate(
                        (row["p"][method] for row in positive_rows if row["k"] == k), alpha
                    )
                    for k in scorer.ALL_K
                }
                for alpha in scorer.ALPHAS
            },
        }

    candidate = metrics[sparse_tail.METHOD_ID]
    fixed4 = metrics[FIXED4_ID]
    wavelet_metrics = metrics[WAVELET_ID]
    recall_not_below_both = {
        str(k): candidate["recall"]["0.05"][str(k)]
        >= min(
            fixed4["recall"]["0.05"][str(k)],
            wavelet_metrics["recall"]["0.05"][str(k)],
        )
        for k in scorer.ALL_K
    }
    promotion_gates = {
        "weak_auc_exceeds_wavelet": candidate["weak_auc"] > wavelet_metrics["weak_auc"],
        "k4_recall_005_exceeds_wavelet": (
            candidate["recall"]["0.05"]["4"] > wavelet_metrics["recall"]["0.05"]["4"]
        ),
        "recall_005_not_below_both_components_for_every_k": all(recall_not_below_both.values()),
        "fpr_005_at_most_0065": candidate["fpr"]["0.05"] <= 0.065,
        "fpr_001_at_most_002": candidate["fpr"]["0.01"] <= 0.02,
        "worst_sector_fpr_005_at_most_008": candidate["worst_sector_fpr_005"] <= 0.08,
    }
    balanced_recall = {
        method: float(np.mean([metrics[method]["recall"]["0.05"][str(k)] for k in scorer.ALL_K]))
        for method in METHODS
    }
    if all(promotion_gates.values()):
        decision = "PROMOTE_SPARSE_TAIL_AUGMENTATION"
    elif (
        candidate["weak_auc"] > wavelet_metrics["weak_auc"]
        or balanced_recall[sparse_tail.METHOD_ID] > balanced_recall[WAVELET_ID]
    ):
        decision = "RETAIN_AS_OPTIONAL_SPARSE_TAIL_AUGMENTATION"
    else:
        decision = "REJECT_SPARSE_TAIL_AUGMENTATION"

    execution_gates = {
        "protocol_frozen_before_2021_scores": (
            protocol["status"] == "frozen_before_any_sonotaco_2021_component_or_sparse_tail_score"
        ),
        "eligibility_frozen_before_2021_scores": eligibility["gates"]["no_detector_score_computed"] is True,
        "parser_all_pass": all(bool(value) for value in parser_audit["gates"].values()),
        "supported_bins_exact": tuple(supported_bins) == EXPECTED_SUPPORTED_BINS,
        "eligible_showers_exact": tuple(eligible_showers) == EXPECTED_ELIGIBLE_SHOWERS,
        "episode_counts_exact": (
            len(calibration_rows) == EXPECTED_CALIBRATION_EPISODES
            and len(negative_rows) == EXPECTED_NEGATIVE_EPISODES
            and len(positive_rows) == EXPECTED_POSITIVE_EPISODES
        ),
        "all_five_folds_nonempty": all(bool(fold_units[fold]) for fold in range(base.N_FOLDS)),
        "wavelet_rules_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
        "sparse_tail_rule_unchanged": (
            sparse_tail.METHOD_ID == "wavelet_primary_fixed4_margin_025"
            and sparse_tail.MARGIN == 0.25
            and all(sparse_tail.self_test().values())
        ),
        "all_scores_pvalues_and_metrics_finite": (
            all(
                np.isfinite(value)
                for row in calibration_rows + negative_rows + positive_rows
                for value in row["scores"].values()
            )
            and all(
                0.0 < float(value) <= 1.0
                for row in negative_rows + positive_rows
                for value in row["p"].values()
            )
            and all(np.isfinite(metrics[method]["weak_auc"]) for method in METHODS)
        ),
    }
    verdict = (
        "PASS_SONOTACO_2021_PROSPECTIVE_SPARSE_TAIL_VALIDATION"
        if all(execution_gates.values())
        else "FAIL_SONOTACO_2021_PROSPECTIVE_SPARSE_TAIL_VALIDATION"
    )
    result = {
        "verdict": verdict,
        "decision": decision,
        "classification": (
            "sole prospective validation of the frozen wavelet-primary fixed4 margin augmentation; "
            "method and promotion gates frozen before 2021 score access"
        ),
        "configuration": {
            "year": YEAR,
            "corpus": CORPUS,
            "methods": list(METHODS),
            "supported_bins": supported_bins,
            "eligible_showers": len(eligible_showers),
            "calibration_per_bin": scorer.CALIBRATION_NEGATIVES_PER_BIN,
            "negative_per_bin": scorer.TEST_NEGATIVES_PER_BIN,
            "positive_replicates": scorer.POSITIVE_REPLICATES,
            "member_counts": list(scorer.ALL_K),
            "sparse_tail_margin": sparse_tail.MARGIN,
        },
        "input_hashes": {
            "archive_sha256": sha256_bytes(args.archive.read_bytes()),
            "mapping_audit_sha256": sha256_bytes(args.audit.read_bytes()),
            "confirmation_source_sha256": sha256_bytes(args.confirmation_source.read_bytes()),
            "wavelet_source_sha256": sha256_bytes(Path(wavelet.__file__).read_bytes()),
            "sparse_tail_source_sha256": sha256_bytes(Path(sparse_tail.__file__).read_bytes()),
            "protocol_sha256": sha256_bytes(args.protocol.read_bytes()),
            "eligibility_freeze_sha256": sha256_bytes(args.eligibility_freeze.read_bytes()),
        },
        "parser_audit": parser_audit,
        "metrics": metrics,
        "prospective_decision": {
            "promotion_gates": promotion_gates,
            "recall_not_below_both_by_k_at_005": recall_not_below_both,
            "balanced_recall_at_005": balanced_recall,
            "frozen_decision": decision,
        },
        "execution_gates": execution_gates,
        "claim_boundary": protocol["claim_boundary"],
    }
    output_json = args.output / "sonotaco_2021_sparse_tail_validation.json"
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, rows in (("negative", negative_rows), ("positive", positive_rows)):
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows).encode()
        (args.output / f"{name}_sparse_tail_records.jsonl.gz").write_bytes(gzip.compress(payload))

    lines = [
        "# SonotaCo 2021 prospective sparse-tail augmentation validation",
        "",
        f"Verdict: **`{verdict}`**",
        f"Frozen decision: **`{decision}`**",
        "",
        "| Method | Weak AUROC | FPR .05 | FPR .01 | Worst-sector FPR .05 |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        row = metrics[method]
        lines.append(
            f"| `{method}` | {row['weak_auc']:.6f} | {row['fpr']['0.05']:.6f} | "
            f"{row['fpr']['0.01']:.6f} | {row['worst_sector_fpr_005']:.6f} |"
        )
    lines.extend(["", "## Recall at alpha .05", ""])
    for method in METHODS:
        row = metrics[method]["recall"]["0.05"]
        lines.append(
            f"- `{method}` — k=4/6/8/12: "
            + ", ".join(f"{row[str(k)]:.6f}" for k in scorer.ALL_K)
        )
    lines.extend([
        "",
        "The promotion decision was computed from the preregistered gates without post-result adjustment.",
    ])
    (args.output / "SONOTACO_2021_SPARSE_TAIL_VALIDATION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    if not all(execution_gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
