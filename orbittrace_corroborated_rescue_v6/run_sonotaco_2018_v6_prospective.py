#!/usr/bin/env python3
"""Run the single frozen OrbitTrace-v6 prospective validation on SonotaCo 2018.

The runner evaluates only frozen fixed4, frozen Brown-family wavelet, and frozen
OrbitTrace v3 scores. V6 uses all 512 calibration nulls per supported bin while
predecessor references use the deterministic first-128 prefix.
"""
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

import wavelet_episode_comparator as wavelet
import multi_anchor_energy_v3 as v3
import decision_v6 as decision

YEAR = 2018
CORPUS = "sonotaco-2018-v6-prospective-validation"
BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
SCORER_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
CANDIDATE_SOURCE_SHA256 = "747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301"
CALIBRATION_512 = 512
PREDECESSOR_128 = 128
V6_DENOMINATOR = 513
PREDECESSOR_DENOMINATOR = 129
FPR_CAP = 0.055
SECTOR_FPR_CAP = 0.08
RECALL_TOLERANCE = 0.03
METHOD_FIXED4 = "orbittrace_fixed4"
METHOD_BROWN = "brown2010_wavelet_episode_core"
METHOD_V3 = "orbittrace_multi_anchor_wavelet_energy_v3"
METHODS = (METHOD_FIXED4, METHOD_BROWN, METHOD_V3)

_WORKER_BASE: types.ModuleType | None = None
_WORKER_SCORER: types.ModuleType | None = None
_WORKER_CANDIDATE: types.ModuleType | None = None
_WORKER_MONDRIAN: Any = None
_WORKER_POSITIVE: Any = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
    parser.add_argument("--confirmation-source", required=True, type=Path)
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
        raise RuntimeError(f"unexpected source parts under {path}: {[p.name for p in parts]}")
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


def conservative_rank_pvalue(score: float, calibration_scores: Iterable[float]) -> float:
    calibration = np.asarray(list(calibration_scores), dtype=np.float64)
    if not len(calibration) or not np.all(np.isfinite(calibration)):
        raise ValueError("invalid calibration panel")
    return float((1 + np.sum(calibration >= float(score))) / (len(calibration) + 1))


def auc(positive: Iterable[float], negative: Iterable[float]) -> float:
    pos = list(positive)
    neg = list(negative)
    if not pos or not neg:
        raise ValueError("AUROC requires non-empty classes")
    y = np.asarray([1] * len(pos) + [0] * len(neg), dtype=np.int8)
    scores = np.asarray(pos + neg, dtype=np.float64)
    if not np.all(np.isfinite(scores)):
        raise ValueError("non-finite AUROC score")
    return float(roc_auc_score(y, scores))


def on_grid(value: float, denominator: int, tolerance: float = 1e-12) -> bool:
    rank = round(float(value) * denominator)
    return rank >= 1 and abs(float(value) - rank / denominator) <= tolerance


def rate(flags: Iterable[bool]) -> float:
    values = list(bool(flag) for flag in flags)
    if not values:
        return float("nan")
    return float(np.mean(values))


def score_episode(episode: Any) -> dict[str, float]:
    if _WORKER_BASE is None or _WORKER_CANDIDATE is None:
        raise RuntimeError("worker score state unavailable")
    fixed_scores, _selected = _WORKER_CANDIDATE.scores_for_episode(_WORKER_BASE, episode)
    scores = {
        METHOD_FIXED4: float(fixed_scores["4"]),
        METHOD_BROWN: float(wavelet.wavelet_episode_score(episode)),
        METHOD_V3: float(v3.multi_anchor_energy_episode_score(episode)),
    }
    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):
        raise RuntimeError(f"invalid score row: {scores}")
    return scores


def score_background(task: tuple[str, int, int]) -> dict[str, Any]:
    if _WORKER_MONDRIAN is None or _WORKER_SCORER is None:
        raise RuntimeError("worker background state unavailable")
    kind, bin_index, index = task
    prefix = "mondrian-development-calibration" if kind == "calibration" else "mondrian-development-negative"
    episode = _WORKER_MONDRIAN.make(
        YEAR,
        bin_index,
        _WORKER_SCORER.stable_seed(prefix, CORPUS, YEAR, bin_index, index),
    )
    return {
        "kind": kind,
        "bin": int(bin_index),
        "index": int(index),
        "center_sol": float(episode.center_sol),
        "scores": score_episode(episode),
    }


def score_positive(task: tuple[int, int, int, int, int, str]) -> dict[str, Any]:
    if _WORKER_POSITIVE is None or _WORKER_SCORER is None or _WORKER_BASE is None:
        raise RuntimeError("worker positive state unavailable")
    shower, year, k, replicate, fold, complex_key = task
    episode = _WORKER_SCORER.make_positive(
        _WORKER_BASE,
        _WORKER_POSITIVE,
        shower,
        year,
        k,
        _WORKER_SCORER.stable_seed("mondrian-development-positive", CORPUS, shower, year, k, replicate),
    )
    return {
        "shower": int(shower),
        "year": int(year),
        "k": int(k),
        "replicate": int(replicate),
        "fold": int(fold),
        "complex_key": str(complex_key),
        "bin": int(_WORKER_SCORER.mondrian_bin_of(episode.center_sol)),
        "center_sol": float(episode.center_sol),
        "scores": score_episode(episode),
    }


def dump_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n" for row in rows).encode()
    path.write_bytes(gzip.compress(payload))


def main() -> None:
    global _WORKER_BASE, _WORKER_SCORER, _WORKER_CANDIDATE, _WORKER_MONDRIAN, _WORKER_POSITIVE

    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    eligibility = json.loads(args.eligibility_freeze.read_text(encoding="utf-8"))
    if eligibility.get("verdict") != "PASS_SONOTACO_2018_V6_ELIGIBILITY_AUDIT":
        raise RuntimeError("invalid 2018 eligibility freeze verdict")
    if eligibility.get("scientific_scores_computed") is not False:
        raise RuntimeError("eligibility freeze was not pre-scoring")
    if int(eligibility.get("year")) != YEAR or eligibility.get("corpus") != CORPUS:
        raise RuntimeError("eligibility freeze corpus mismatch")
    constants = eligibility["benchmark_constants"]
    if constants != {
        "calibration_per_bin": 512,
        "calibration_denominator": 513,
        "negative_per_bin": 64,
        "positive_replicates": 4,
        "member_counts": [4, 6, 8, 12],
        "folds": 5,
        "primary_v3_max_rank": 17,
        "fixed4_max_rank": 15,
        "corroboration_v3_max_rank": 122,
        "decision_rule": "(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))",
    }:
        raise RuntimeError(f"eligibility constants mismatch: {constants}")

    base = load_module("v6_2018_base", decode_file(args.baseline_payload), BASELINE_SOURCE_SHA256)
    scorer = load_module(
        "v6_2018_scorer",
        decode_parts(args.scorer_parts, ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]),
        SCORER_SOURCE_SHA256,
    )
    candidate = load_module("v6_2018_candidate", decode_file(args.candidate_payload), CANDIDATE_SOURCE_SHA256)
    if int(scorer.CALIBRATION_NEGATIVES_PER_BIN) != PREDECESSOR_128:
        raise RuntimeError(f"unexpected predecessor calibration size: {scorer.CALIBRATION_NEGATIVES_PER_BIN}")
    scorer.CALIBRATION_NEGATIVES_PER_BIN = CALIBRATION_512

    confirmation_payload = args.confirmation_source.read_bytes()
    confirmation_hash = sha256_bytes(confirmation_payload)
    if confirmation_hash != eligibility["parser"]["sonotaco_2018_confirmation_source_sha256"]:
        raise RuntimeError(f"2018 parser hash mismatch: {confirmation_hash}")
    confirmation = load_module("v6_2018_confirmation", confirmation_payload)
    parse_2018 = getattr(confirmation, "parse_sonotaco_2018_events")
    labeled, sporadic, parser_audit = parse_2018(args.archive, args.audit, base)
    if not all(bool(value) for value in parser_audit["gates"].values()):
        raise RuntimeError(f"2018 parser audit failed: {parser_audit['gates']}")

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
    frozen_bins = [int(value) for value in eligibility["counts"]["supported_bins"]]
    if supported_bins != frozen_bins:
        raise RuntimeError(f"supported-bin universe changed: {supported_bins} != {frozen_bins}")

    positive_factory = base.EpisodeFactory(labeled, sporadic)
    fold_mapping, fold_units = base.assign_folds(labeled)
    eligible_showers = sorted(int(value) for value in positive_factory.shower_years)
    frozen_showers = [int(value) for value in eligibility["counts"]["eligible_showers"]]
    if eligible_showers != frozen_showers:
        raise RuntimeError(f"eligible shower universe changed: {eligible_showers} != {frozen_showers}")

    fold_unit_counts = {str(fold): len(fold_units[fold]) for fold in range(base.N_FOLDS)}
    if fold_unit_counts != eligibility["counts"]["fold_unit_counts"]:
        raise RuntimeError(f"fold-unit universe changed: {fold_unit_counts}")
    positive_counts_by_fold = {str(fold): 0 for fold in range(base.N_FOLDS)}
    for shower in eligible_showers:
        fold = int(fold_mapping[positive_factory.shower_complex[shower]])
        positive_counts_by_fold[str(fold)] += (
            len(positive_factory.shower_years[shower]) * len(scorer.ALL_K) * scorer.POSITIVE_REPLICATES
        )
    if positive_counts_by_fold != eligibility["counts"]["positive_episode_counts_by_fold"]:
        raise RuntimeError(f"positive fold universe changed: {positive_counts_by_fold}")

    _WORKER_BASE = base
    _WORKER_SCORER = scorer
    _WORKER_CANDIDATE = candidate
    _WORKER_MONDRIAN = mondrian
    _WORKER_POSITIVE = positive_factory

    calibration_tasks = [
        ("calibration", bin_index, index)
        for bin_index in supported_bins
        for index in range(CALIBRATION_512)
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
    expected = eligibility["counts"]
    if len(calibration_tasks) != int(expected["calibration_episodes"]):
        raise RuntimeError("calibration task count differs from eligibility freeze")
    if len(negative_tasks) != int(expected["negative_episodes"]):
        raise RuntimeError("negative task count differs from eligibility freeze")
    if len(positive_tasks) != int(expected["positive_episodes"]):
        raise RuntimeError("positive task count differs from eligibility freeze")

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

    if len(calibration_rows) != int(expected["calibration_episodes"]):
        raise RuntimeError("calibration execution count differs from freeze")
    if len(negative_rows) != int(expected["negative_episodes"]):
        raise RuntimeError("negative execution count differs from freeze")
    if len(positive_rows) != int(expected["positive_episodes"]):
        raise RuntimeError("positive execution count differs from freeze")

    calibration_512: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}
    calibration_128: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}
    for method in METHODS:
        for bin_index in supported_bins:
            rows = sorted(
                (row for row in calibration_rows if row["bin"] == bin_index),
                key=lambda row: int(row["index"]),
            )
            if [int(row["index"]) for row in rows] != list(range(CALIBRATION_512)):
                raise RuntimeError(f"calibration index universe mismatch method={method} bin={bin_index}")
            values = np.asarray([row["scores"][method] for row in rows], dtype=np.float64)
            if len(values) != CALIBRATION_512 or not np.all(np.isfinite(values)):
                raise RuntimeError(f"invalid 512 calibration panel method={method} bin={bin_index}")
            calibration_512[method][bin_index] = values
            calibration_128[method][bin_index] = values[:PREDECESSOR_128].copy()

    for row in negative_rows:
        bin_index = int(row["bin"])
        row["reporting_sector"] = int(scorer.reporting_sector_of(row["center_sol"]))
        row["p_v6"] = {
            METHOD_V3: conservative_rank_pvalue(row["scores"][METHOD_V3], calibration_512[METHOD_V3][bin_index]),
            METHOD_FIXED4: conservative_rank_pvalue(row["scores"][METHOD_FIXED4], calibration_512[METHOD_FIXED4][bin_index]),
        }
        row["p_predecessor"] = {
            METHOD_BROWN: conservative_rank_pvalue(row["scores"][METHOD_BROWN], calibration_128[METHOD_BROWN][bin_index]),
            METHOD_FIXED4: conservative_rank_pvalue(row["scores"][METHOD_FIXED4], calibration_128[METHOD_FIXED4][bin_index]),
        }
        row["v6_detected"] = bool(decision.detected(row["p_v6"][METHOD_V3], row["p_v6"][METHOD_FIXED4]))

    for row in positive_rows:
        bin_index = int(row["bin"])
        if bin_index not in supported_bins:
            raise RuntimeError(f"positive maps to unsupported bin {bin_index}")
        row["p_v6"] = {
            METHOD_V3: conservative_rank_pvalue(row["scores"][METHOD_V3], calibration_512[METHOD_V3][bin_index]),
            METHOD_FIXED4: conservative_rank_pvalue(row["scores"][METHOD_FIXED4], calibration_512[METHOD_FIXED4][bin_index]),
        }
        row["p_predecessor"] = {
            METHOD_BROWN: conservative_rank_pvalue(row["scores"][METHOD_BROWN], calibration_128[METHOD_BROWN][bin_index]),
            METHOD_FIXED4: conservative_rank_pvalue(row["scores"][METHOD_FIXED4], calibration_128[METHOD_FIXED4][bin_index]),
        }
        row["v6_detected"] = bool(decision.detected(row["p_v6"][METHOD_V3], row["p_v6"][METHOD_FIXED4]))

    v6_grid_exact = all(
        on_grid(row["p_v6"][method], V6_DENOMINATOR)
        for row in negative_rows + positive_rows
        for method in (METHOD_V3, METHOD_FIXED4)
    )
    predecessor_grid_exact = all(
        on_grid(row["p_predecessor"][method], PREDECESSOR_DENOMINATOR)
        for row in negative_rows + positive_rows
        for method in (METHOD_BROWN, METHOD_FIXED4)
    )

    weak_k = set(int(value) for value in scorer.WEAK_K)
    weak_positive = [row for row in positive_rows if int(row["k"]) in weak_k]
    raw_auc = {
        method: auc(
            (row["scores"][method] for row in weak_positive),
            (row["scores"][method] for row in negative_rows),
        )
        for method in METHODS
    }

    v6_fpr = rate(row["v6_detected"] for row in negative_rows)
    sector_fpr = {
        str(sector): rate(
            row["v6_detected"]
            for row in negative_rows
            if int(row["reporting_sector"]) == sector
        )
        for sector in sorted({int(row["reporting_sector"]) for row in negative_rows})
    }
    worst_sector_fpr = max(sector_fpr.values())
    v6_recall = {
        str(k): rate(row["v6_detected"] for row in positive_rows if int(row["k"]) == int(k))
        for k in scorer.ALL_K
    }
    fixed4_reference_recall = {
        str(k): rate(
            row["p_predecessor"][METHOD_FIXED4] <= 0.05
            for row in positive_rows
            if int(row["k"]) == int(k)
        )
        for k in scorer.ALL_K
    }
    brown_reference_recall = {
        str(k): rate(
            row["p_predecessor"][METHOD_BROWN] <= 0.05
            for row in positive_rows
            if int(row["k"]) == int(k)
        )
        for k in scorer.ALL_K
    }
    predecessor_fpr = {
        METHOD_FIXED4: rate(row["p_predecessor"][METHOD_FIXED4] <= 0.05 for row in negative_rows),
        METHOD_BROWN: rate(row["p_predecessor"][METHOD_BROWN] <= 0.05 for row in negative_rows),
    }

    exact_decision_rule = (
        decision.CALIBRATION_NEGATIVES_PER_BIN == 512
        and decision.CALIBRATION_DENOMINATOR == 513
        and decision.PRIMARY_V3_MAX_RANK == 17
        and decision.FIXED4_MAX_RANK == 15
        and decision.CORROBORATION_V3_MAX_RANK == 122
        and all(decision.self_test().values())
    )
    gates = {
        "parser_all_pass": all(bool(value) for value in parser_audit["gates"].values()),
        "eligibility_universe_exact": (
            supported_bins == frozen_bins
            and eligible_showers == frozen_showers
            and len(calibration_rows) == int(expected["calibration_episodes"])
            and len(negative_rows) == int(expected["negative_episodes"])
            and len(positive_rows) == int(expected["positive_episodes"])
            and fold_unit_counts == expected["fold_unit_counts"]
            and positive_counts_by_fold == expected["positive_episode_counts_by_fold"]
        ),
        "frozen_scoring_sources_self_test": (
            all(wavelet.self_test().values())
            and all(v3.self_test().values())
            and exact_decision_rule
        ),
        "calibration_panels_exact_512_and_prefix128": all(
            len(calibration_512[method][bin_index]) == 512
            and len(calibration_128[method][bin_index]) == 128
            and np.array_equal(calibration_128[method][bin_index], calibration_512[method][bin_index][:128])
            for method in METHODS
            for bin_index in supported_bins
        ),
        "v6_pvalues_exact_denominator_513_grid": v6_grid_exact,
        "predecessor_pvalues_exact_denominator_129_grid": predecessor_grid_exact,
        "v3_weak_auc_at_least_brown": raw_auc[METHOD_V3] + 1e-15 >= raw_auc[METHOD_BROWN],
        "v6_pooled_fpr_at_most_0055": v6_fpr <= FPR_CAP + 1e-15,
        "v6_worst_sector_fpr_at_most_008": worst_sector_fpr <= SECTOR_FPR_CAP + 1e-15,
        "v6_k4_recall_at_least_predecessor_fixed4": v6_recall["4"] + 1e-15 >= fixed4_reference_recall["4"],
        "v6_k6_within_003_of_predecessor_brown": v6_recall["6"] + 1e-15 >= brown_reference_recall["6"] - RECALL_TOLERANCE,
        "v6_k8_within_003_of_predecessor_brown": v6_recall["8"] + 1e-15 >= brown_reference_recall["8"] - RECALL_TOLERANCE,
        "v6_k12_within_003_of_predecessor_brown": v6_recall["12"] + 1e-15 >= brown_reference_recall["12"] - RECALL_TOLERANCE,
        "v6_decision_rule_exact_17_15_122_over_513": exact_decision_rule,
    }
    verdict = (
        "PASS_V6_SONOTACO_2018_PROSPECTIVE_VALIDATION"
        if all(gates.values())
        else "FAIL_V6_SONOTACO_2018_PROSPECTIVE_VALIDATION"
    )

    result = {
        "verdict": verdict,
        "classification": "single preregistered prospective validation of frozen OrbitTrace-v6 sparse-episode detector",
        "configuration": {
            "year": YEAR,
            "corpus": CORPUS,
            "methods": list(METHODS),
            "weak_k": sorted(weak_k),
            "supported_bins": supported_bins,
            "eligible_showers": eligible_showers,
            "calibration_per_bin_v6": CALIBRATION_512,
            "calibration_denominator_v6": V6_DENOMINATOR,
            "calibration_per_bin_predecessor": PREDECESSOR_128,
            "calibration_denominator_predecessor": PREDECESSOR_DENOMINATOR,
            "primary_v3_max_rank": decision.PRIMARY_V3_MAX_RANK,
            "fixed4_max_rank": decision.FIXED4_MAX_RANK,
            "corroboration_v3_max_rank": decision.CORROBORATION_V3_MAX_RANK,
            "decision_rule": "(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))",
            "predecessor_nominal_alpha": 0.05,
            "fpr_cap": FPR_CAP,
            "sector_fpr_cap": SECTOR_FPR_CAP,
            "recall_tolerance": RECALL_TOLERANCE,
        },
        "input_hashes": {
            "archive_sha256": eligibility["transport"]["archive_sha256"],
            "member_sha256": eligibility["transport"]["member_sha256"],
            "mapping_audit_sha256": eligibility["transport"]["mapping_audit_sha256"],
            "confirmation_source_sha256": confirmation_hash,
            "eligibility_freeze_sha256": sha256_bytes(args.eligibility_freeze.read_bytes()),
        },
        "counts": {
            "labeled_events": len(labeled),
            "sporadic_events": len(sporadic),
            "calibration_episodes": len(calibration_rows),
            "negative_episodes": len(negative_rows),
            "positive_episodes": len(positive_rows),
            "fold_unit_counts": fold_unit_counts,
            "positive_episode_counts_by_fold": positive_counts_by_fold,
        },
        "raw_auc": raw_auc,
        "v3_minus_brown_weak_auc": raw_auc[METHOD_V3] - raw_auc[METHOD_BROWN],
        "v6": {
            "pooled_fpr": v6_fpr,
            "sector_fpr": sector_fpr,
            "worst_sector_fpr": worst_sector_fpr,
            "recall": v6_recall,
        },
        "predecessor_references": {
            "calibration_prefix": "first 128 of the frozen 512-null seed sequence",
            "nominal_alpha": 0.05,
            "fpr": predecessor_fpr,
            "fixed4_recall": fixed4_reference_recall,
            "brown_recall": brown_reference_recall,
        },
        "parser_audit": parser_audit,
        "gates": gates,
        "claim_boundary": (
            "A pass promotes v6 as a prospectively validated sparse-episode detector only; "
            "blind catalogue rediscovery and OrbitTrace target recovery remain separate tests."
        ),
    }

    (args.output / "SONOTACO_2018_V6_PROSPECTIVE_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    dump_jsonl_gz(args.output / "calibration_records.jsonl.gz", calibration_rows)
    dump_jsonl_gz(args.output / "negative_records.jsonl.gz", negative_rows)
    dump_jsonl_gz(args.output / "positive_records.jsonl.gz", positive_rows)

    lines = [
        "# OrbitTrace v6 SonotaCo 2018 prospective validation",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        "## Continuous ranking",
        "",
        f"- v3 weak AUROC: **{raw_auc[METHOD_V3]:.6f}**",
        f"- Brown-family weak AUROC: **{raw_auc[METHOD_BROWN]:.6f}**",
        f"- fixed4 weak AUROC: **{raw_auc[METHOD_FIXED4]:.6f}**",
        f"- v3 - Brown: **{raw_auc[METHOD_V3] - raw_auc[METHOD_BROWN]:+.6f}**",
        "",
        "## Frozen v6 decision",
        "",
        f"- pooled FPR: **{v6_fpr:.6f}**",
        f"- worst-sector FPR: **{worst_sector_fpr:.6f}**",
        "- recall k=4/6/8/12: **" + " / ".join(f"{v6_recall[str(k)]:.6f}" for k in scorer.ALL_K) + "**",
        "",
        "## Predecessor references (first 128 nulls, denominator 129, nominal alpha .05)",
        "",
        "- fixed4 recall k=4/6/8/12: **" + " / ".join(f"{fixed4_reference_recall[str(k)]:.6f}" for k in scorer.ALL_K) + "**",
        "- Brown recall k=4/6/8/12: **" + " / ".join(f"{brown_reference_recall[str(k)]:.6f}" for k in scorer.ALL_K) + "**",
        f"- fixed4 FPR: **{predecessor_fpr[METHOD_FIXED4]:.6f}**",
        f"- Brown FPR: **{predecessor_fpr[METHOD_BROWN]:.6f}**",
        "",
        "## Gates",
        "",
    ]
    for name, passed in gates.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`")
    lines.extend([
        "",
        "This is the one preregistered SonotaCo 2018 prospective execution. No same-corpus retuning is authorized.",
        "",
        "A passing result validates the sparse-episode detector; it does not by itself establish blind catalogue rediscovery or OrbitTrace target recovery.",
    ])
    (args.output / "SONOTACO_2018_V6_PROSPECTIVE_RESULT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
