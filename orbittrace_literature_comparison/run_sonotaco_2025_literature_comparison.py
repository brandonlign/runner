#!/usr/bin/env python3
"""Run the frozen SonotaCo-2025 episode-track literature comparison."""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
import multiprocessing as mp
import os
import sys
import types
import zipfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import roc_auc_score

import literature_comparators as literature

YEAR = 2025
CORPUS = "sonotaco-2025-native"
MEMBER = "025a/_U2_20250101_S.csv"
ARCHIVE_SHA256 = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
MEMBER_SHA256 = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
BASELINE_SOURCE_SHA256 = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
SCORER_SOURCE_SHA256 = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
ADAPTER_SOURCE_SHA256 = "5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518"
CANDIDATE_SOURCE_SHA256 = "747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301"
EXPECTED_FIXED4_WEAK_AUC = 0.813250
EXPECTED_INTERNAL_AUC = {
    "internal_split": 0.7566540287990197,
    "internal_density": 0.7539780560661765,
    "internal_dbscan": 0.7494865866268382,
}
METHODS = (
    "orbittrace_fixed4",
    "internal_split",
    "internal_density",
    "internal_dbscan",
    "sugar2017_core_transfer",
    "rudawska2014_dsh6",
    "dsh4_sparse_adaptation",
)

_WORKER_BASE: types.ModuleType | None = None
_WORKER_SCORER: types.ModuleType | None = None
_WORKER_CANDIDATE: types.ModuleType | None = None
_WORKER_MONDRIAN: Any = None
_WORKER_POSITIVE: Any = None
_WORKER_SUGAR_EPSILON: float | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--baseline-payload", required=True, type=Path)
    parser.add_argument("--scorer-parts", required=True, type=Path)
    parser.add_argument("--adapter-parts", required=True, type=Path)
    parser.add_argument("--candidate-payload", required=True, type=Path)
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


def load_module(name: str, source: bytes, expected_hash: str) -> types.ModuleType:
    digest = sha256_bytes(source)
    if digest != expected_hash:
        raise RuntimeError(f"{name} source mismatch: {digest}")
    module = types.ModuleType(name)
    module.__file__ = f"{name}.py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def load_sources(args: argparse.Namespace) -> tuple[types.ModuleType, types.ModuleType, types.ModuleType, types.ModuleType]:
    return (
        load_module("literature_base", decode_file(args.baseline_payload), BASELINE_SOURCE_SHA256),
        load_module(
            "literature_scorer",
            decode_parts(args.scorer_parts, ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]),
            SCORER_SOURCE_SHA256,
        ),
        load_module(
            "literature_adapter",
            decode_parts(args.adapter_parts, ["part00.b64"]),
            ADAPTER_SOURCE_SHA256,
        ),
        load_module("literature_candidate", decode_file(args.candidate_payload), CANDIDATE_SOURCE_SHA256),
    )


def parse_float(value: str) -> float:
    result = float(value.strip())
    if not np.isfinite(result):
        raise ValueError(value)
    return result


def load_orbit_sidecars(archive: Path) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    archive_hash = sha256_bytes(archive.read_bytes())
    if archive_hash != ARCHIVE_SHA256:
        raise RuntimeError(f"archive hash mismatch: {archive_hash}")
    with zipfile.ZipFile(archive) as handle:
        payload = handle.read(MEMBER)
    member_hash = sha256_bytes(payload)
    if member_hash != MEMBER_SHA256:
        raise RuntimeError(f"member hash mismatch: {member_hash}")
    reader = csv.reader(io.StringIO(payload.decode("utf-8-sig"), newline=""), delimiter=",")
    header = [field.strip() for field in next(reader)]
    index = {field: position for position, field in enumerate(header)}
    required = {
        "ra sd(deg)", "de sd(deg)", "vg sd(km/s)",
        "q(AU)", "e", "peri(deg)", "node(deg)", "incl(deg)",
        "q sd(AU)", "e sd", "peri sd(deg)", "incl sd(deg)",
    }
    if not required.issubset(index):
        raise RuntimeError(f"sidecar fields missing: {sorted(required.difference(index))}")
    sidecars: dict[str, dict[str, float]] = {}
    malformed = 0
    for row_index, row in enumerate(reader):
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        if len(row) != len(header):
            malformed += 1
            continue
        try:
            record = {
                "ra_sd": parse_float(row[index["ra sd(deg)"]]),
                "dec_sd": parse_float(row[index["de sd(deg)"]]),
                "vg_sd": parse_float(row[index["vg sd(km/s)"]]),
                "orbit_q": parse_float(row[index["q(AU)"]]),
                "orbit_e": parse_float(row[index["e"]]),
                "orbit_peri": parse_float(row[index["peri(deg)"]]) % 360.0,
                "orbit_node": parse_float(row[index["node(deg)"]]) % 360.0,
                "orbit_incl": parse_float(row[index["incl(deg)"]]),
                "orbit_q_sd": parse_float(row[index["q sd(AU)"]]),
                "orbit_e_sd": parse_float(row[index["e sd"]]),
                "orbit_peri_sd": parse_float(row[index["peri sd(deg)"]]),
                "orbit_incl_sd": parse_float(row[index["incl sd(deg)"]]),
            }
        except (ValueError, IndexError):
            continue
        if not (
            record["orbit_q"] > 0.0
            and record["orbit_e"] >= 0.0
            and 0.0 <= record["orbit_incl"] <= 180.0
            and record["ra_sd"] >= 0.0
            and record["dec_sd"] >= 0.0
            and record["vg_sd"] >= 0.0
        ):
            continue
        sidecars[f"SNM2025:{row_index}"] = record
    return sidecars, {
        "archive_sha256": archive_hash,
        "member_sha256": member_hash,
        "header_fields": len(header),
        "sidecar_rows": len(sidecars),
        "malformed_rows": malformed,
    }


def attach_sidecars(events: list[dict[str, Any]], sidecars: dict[str, dict[str, float]]) -> int:
    missing: list[str] = []
    for event in events:
        event_id = str(event["id"])
        record = sidecars.get(event_id)
        if record is None:
            missing.append(event_id)
            continue
        event.update(record)
    if missing:
        raise RuntimeError(f"missing valid orbital sidecars for {len(missing)} benchmark events; first={missing[:5]}")
    return len(events)


def install_episode_sidecars(base: types.ModuleType) -> None:
    original = base.make_episode

    def wrapped(
        members: list[dict[str, Any]],
        sporadic: list[dict[str, Any]],
        center: float,
        shower: int,
        complex_key: str,
        year: int,
    ) -> Any:
        episode = original(members, sporadic, center, shower, complex_key, year)
        raw_events = members + sporadic
        rng = np.random.default_rng(
            base.stable_seed("shuffle", shower, year, center, *(str(event["id"]) for event in raw_events[:4]))
        )
        order = rng.permutation(len(raw_events))
        events = [raw_events[int(index)] for index in order]
        expected_membership = np.asarray([1] * len(members) + [0] * len(sporadic), dtype=np.int8)[order]
        if not np.array_equal(expected_membership, episode.membership):
            raise RuntimeError("episode-sidecar order differs from frozen episode order")
        fields = {
            "event_ids": ("id", object),
            "ra": ("ra", np.float64),
            "dec": ("dec", np.float64),
            "ra_sd": ("ra_sd", np.float64),
            "dec_sd": ("dec_sd", np.float64),
            "vg_sd": ("vg_sd", np.float64),
            "orbit_q": ("orbit_q", np.float64),
            "orbit_e": ("orbit_e", np.float64),
            "orbit_peri": ("orbit_peri", np.float64),
            "orbit_node": ("orbit_node", np.float64),
            "orbit_incl": ("orbit_incl", np.float64),
            "orbit_q_sd": ("orbit_q_sd", np.float64),
            "orbit_e_sd": ("orbit_e_sd", np.float64),
            "orbit_peri_sd": ("orbit_peri_sd", np.float64),
            "orbit_incl_sd": ("orbit_incl_sd", np.float64),
        }
        for attribute, (key, dtype) in fields.items():
            setattr(episode, attribute, np.asarray([event[key] for event in events], dtype=dtype))
        return episode

    base.make_episode = wrapped


def score_episode(episode: Any, key: object) -> dict[str, float]:
    if _WORKER_BASE is None or _WORKER_SCORER is None or _WORKER_CANDIDATE is None or _WORKER_SUGAR_EPSILON is None:
        raise RuntimeError("worker state unavailable")
    fixed_scores, _selected = _WORKER_CANDIDATE.scores_for_episode(_WORKER_BASE, episode)
    _original, split, density, internal_dbscan = _WORKER_SCORER.score_all(_WORKER_BASE, episode, key)
    scores = {
        "orbittrace_fixed4": float(fixed_scores["4"]),
        "internal_split": float(split),
        "internal_density": float(density),
        "internal_dbscan": float(internal_dbscan),
        "sugar2017_core_transfer": literature.sugar_episode_score(episode, _WORKER_SUGAR_EPSILON),
    }
    scores.update(literature.dsh_episode_scores(episode))
    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):
        raise RuntimeError(f"invalid score row: {scores}")
    return scores


def score_background(task: tuple[str, int, int]) -> dict[str, Any]:
    if _WORKER_MONDRIAN is None or _WORKER_SCORER is None:
        raise RuntimeError("worker background factory unavailable")
    kind, bin_index, index = task
    prefix = "mondrian-development-calibration" if kind == "calibration" else "mondrian-development-negative"
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
        "scores": score_episode(episode, (kind, CORPUS, YEAR, bin_index, index)),
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
        _WORKER_SCORER.stable_seed("mondrian-development-positive", CORPUS, shower, year, k, replicate),
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
        "scores": score_episode(episode, ("positive", CORPUS, shower, year, k, replicate)),
    }


def auc(positive: Iterable[float], negative: Iterable[float]) -> float:
    pos = list(positive)
    neg = list(negative)
    y = np.asarray([1] * len(pos) + [0] * len(neg), dtype=np.int8)
    return float(roc_auc_score(y, np.asarray(pos + neg, dtype=np.float64)))


def close(value: float, expected: float, tolerance: float = 5e-7) -> bool:
    return abs(float(value) - float(expected)) <= tolerance


def main() -> None:
    global _WORKER_BASE, _WORKER_SCORER, _WORKER_CANDIDATE
    global _WORKER_MONDRIAN, _WORKER_POSITIVE, _WORKER_SUGAR_EPSILON

    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    base, scorer, adapter, candidate = load_sources(args)
    labeled, sporadic, parser_audit = adapter.parse_sonotaco_events(args.archive, args.audit, base)
    sidecars, sidecar_audit = load_orbit_sidecars(args.archive)
    sidecar_audit["attached_labeled"] = attach_sidecars(labeled, sidecars)
    sidecar_audit["attached_sporadic"] = attach_sidecars(sporadic, sidecars)
    install_episode_sidecars(base)

    all_events = labeled + sporadic
    sugar_catalog = literature.sugar_feature_matrix_from_arrays(
        [event["sol"] for event in all_events],
        [event["sun_lon"] for event in all_events],
        [event["ecl_lat"] for event in all_events],
        [event["vg"] for event in all_events],
    )
    sugar_epsilon, sugar_knn4 = literature.sugar_transferred_epsilon(sugar_catalog)

    mondrian = scorer.MondrianWindowFactory(base, sporadic)
    supported_bins: list[int] = []
    for bin_index in range(36):
        try:
            mondrian.make(
                YEAR,
                bin_index,
                scorer.stable_seed("mondrian-development-support", CORPUS, YEAR, bin_index),
            )
        except RuntimeError:
            continue
        supported_bins.append(bin_index)
    if len(supported_bins) != 32:
        raise RuntimeError(f"expected 32 supported bins, found {len(supported_bins)}")

    positive_factory = base.EpisodeFactory(labeled, sporadic)
    fold_mapping, fold_units = base.assign_folds(labeled)
    eligible_showers = sorted(positive_factory.shower_years)
    if len(eligible_showers) != 34:
        raise RuntimeError(f"expected 34 eligible showers, found {len(eligible_showers)}")

    _WORKER_BASE = base
    _WORKER_SCORER = scorer
    _WORKER_CANDIDATE = candidate
    _WORKER_MONDRIAN = mondrian
    _WORKER_POSITIVE = positive_factory
    _WORKER_SUGAR_EPSILON = sugar_epsilon

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

    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}
    for method in METHODS:
        for bin_index in supported_bins:
            values = np.asarray(
                [row["scores"][method] for row in calibration_rows if row["bin"] == bin_index],
                dtype=np.float64,
            )
            if len(values) != scorer.CALIBRATION_NEGATIVES_PER_BIN:
                raise RuntimeError(f"calibration mismatch method={method} bin={bin_index}")
            calibration[method][bin_index] = values

    for row in negative_rows:
        row["reporting_sector"] = int(scorer.reporting_sector_of(row["center_sol"]))
        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in METHODS
        }
    for row in positive_rows:
        if row["bin"] not in supported_bins:
            raise RuntimeError(f"positive maps to unsupported bin {row['bin']}")
        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in METHODS
        }

    metrics: dict[str, Any] = {}
    weak = [row for row in positive_rows if row["k"] in scorer.WEAK_K]
    for method in METHODS:
        negative_scores = [row["scores"][method] for row in negative_rows]
        sectors = {
            str(sector): literature.rate(
                (row["p"][method] for row in negative_rows if row["reporting_sector"] == sector),
                0.05,
            )
            for sector in sorted({row["reporting_sector"] for row in negative_rows})
        }
        recall = {
            str(alpha): {
                str(k): literature.rate(
                    (row["p"][method] for row in positive_rows if row["k"] == k),
                    alpha,
                )
                for k in scorer.ALL_K
            }
            for alpha in scorer.ALPHAS
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
                str(alpha): literature.rate((row["p"][method] for row in negative_rows), alpha)
                for alpha in scorer.ALPHAS
            },
            "worst_sector_fpr_005": max(sectors.values()),
            "recall": recall,
        }

    published_decisions = {
        "sugar2017_core_transfer": {
            "negative_detection_rate": float(np.mean([
                row["scores"]["sugar2017_core_transfer"] >= literature.SUGAR_MIN_SAMPLES
                for row in negative_rows
            ])),
            "positive_detection_rate_by_k": {
                str(k): float(np.mean([
                    row["scores"]["sugar2017_core_transfer"] >= literature.SUGAR_MIN_SAMPLES
                    for row in positive_rows if row["k"] == k
                ]))
                for k in scorer.ALL_K
            },
        },
        "rudawska2014_dsh6": {
            "negative_detection_rate": float(np.mean([
                -row["scores"]["rudawska2014_dsh6"] <= literature.RUD2014_DSH_THRESHOLD
                for row in negative_rows
            ])),
            "positive_detection_rate_by_k": {
                str(k): float(np.mean([
                    -row["scores"]["rudawska2014_dsh6"] <= literature.RUD2014_DSH_THRESHOLD
                    for row in positive_rows if row["k"] == k
                ]))
                for k in scorer.ALL_K
            },
        },
    }

    gates = {
        "parser_all_pass": all(bool(value) for value in parser_audit["gates"].values()),
        "sidecars_cover_exact_benchmark_universe": (
            sidecar_audit["attached_labeled"] == len(labeled)
            and sidecar_audit["attached_sporadic"] == len(sporadic)
        ),
        "supported_bins_exact_32": len(supported_bins) == 32,
        "eligible_showers_exact_34": len(eligible_showers) == 34,
        "episode_counts_exact": (
            len(calibration_rows) == 4096
            and len(negative_rows) == 2048
            and len(positive_rows) == 544
        ),
        "fixed4_auc_reproduced": close(metrics["orbittrace_fixed4"]["weak_auc"], EXPECTED_FIXED4_WEAK_AUC),
        "internal_split_auc_reproduced": close(metrics["internal_split"]["weak_auc"], EXPECTED_INTERNAL_AUC["internal_split"]),
        "internal_density_auc_reproduced": close(metrics["internal_density"]["weak_auc"], EXPECTED_INTERNAL_AUC["internal_density"]),
        "internal_dbscan_auc_reproduced": close(metrics["internal_dbscan"]["weak_auc"], EXPECTED_INTERNAL_AUC["internal_dbscan"]),
        "sugar_rule_frozen": literature.SUGAR_MIN_SAMPLES == 5 and literature.SUGAR_EPS_PERCENTILE == 23.0,
        "dsh_rules_frozen": (
            literature.RUD2014_MIN_MEMBERS == 6
            and literature.SPARSE_ADAPTED_MIN_MEMBERS == 4
            and literature.RUD2014_DSH_THRESHOLD == 0.05
        ),
    }
    verdict = "PASS_SONOTACO_2025_LITERATURE_COMPARISON" if all(gates.values()) else "FAIL_SONOTACO_2025_LITERATURE_COMPARISON"
    result = {
        "verdict": verdict,
        "configuration": {
            "year": YEAR,
            "corpus": CORPUS,
            "methods": list(METHODS),
            "supported_bins": supported_bins,
            "eligible_showers": len(eligible_showers),
            "calibration_per_bin": scorer.CALIBRATION_NEGATIVES_PER_BIN,
            "negative_per_bin": scorer.TEST_NEGATIVES_PER_BIN,
            "positive_replicates": scorer.POSITIVE_REPLICATES,
            "sugar_transferred_epsilon": sugar_epsilon,
            "sugar_fourth_neighbor_summary": {
                "count": len(sugar_knn4),
                "minimum": float(np.min(sugar_knn4)),
                "median": float(np.median(sugar_knn4)),
                "p23": float(np.percentile(sugar_knn4, 23.0)),
                "maximum": float(np.max(sugar_knn4)),
            },
        },
        "parser_audit": parser_audit,
        "sidecar_audit": sidecar_audit,
        "metrics": metrics,
        "published_decisions": published_decisions,
        "structural_limits": {
            "sugar_k4": "published min_samples=5 makes a pure four-member injected stream structurally sub-minimum",
            "rudawska_k4": "published minimum_members=6 makes a pure four-member injected stream structurally sub-minimum",
            "catalogue_methods": "published HDBSCAN and CMOR wavelet methods remain on the separate catalogue track",
        },
        "gates": gates,
    }
    (args.output / "sonotaco_2025_literature_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    (args.output / "transferred_parameters.json").write_text(json.dumps({
        "source_corpus": CORPUS,
        "source_year": YEAR,
        "sugar_epsilon": sugar_epsilon,
        "sugar_min_samples": literature.SUGAR_MIN_SAMPLES,
        "sugar_epsilon_percentile": literature.SUGAR_EPS_PERCENTILE,
        "rudawska_dsh_threshold": literature.RUD2014_DSH_THRESHOLD,
        "rudawska_min_members": literature.RUD2014_MIN_MEMBERS,
        "dsh_sparse_adaptation_min_members": literature.SPARSE_ADAPTED_MIN_MEMBERS,
    }, indent=2) + "\n")
    for name, rows in (("negative", negative_rows), ("positive", positive_rows)):
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows).encode()
        (args.output / f"{name}_literature_records.jsonl.gz").write_bytes(gzip.compress(payload))

    lines = [
        "# SonotaCo 2025 literature-method comparison",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"Transferred Sugar epsilon: **{sugar_epsilon:.9f}**",
        "",
        "| Method | Classification | Weak AUROC | FPR .05 | FPR .01 |",
        "|---|---|---:|---:|---:|",
    ]
    classifications = {
        "orbittrace_fixed4": "frozen candidate",
        "internal_split": "internal baseline",
        "internal_density": "internal baseline",
        "internal_dbscan": "internal baseline",
        "sugar2017_core_transfer": "literature published core",
        "rudawska2014_dsh6": "literature implementation",
        "dsh4_sparse_adaptation": "predeclared adaptation",
    }
    for method in METHODS:
        row = metrics[method]
        lines.append(
            f"| `{method}` | {classifications[method]} | {row['weak_auc']:.6f} | "
            f"{row['fpr']['0.05']:.6f} | {row['fpr']['0.01']:.6f} |"
        )
    lines.extend(["", "## Recall", ""])
    for method in METHODS:
        row = metrics[method]["recall"]
        lines.append(
            f"- `{method}` — k=4/6/8/12 at .05: "
            + ", ".join(f"{row['0.05'][str(k)]:.6f}" for k in scorer.ALL_K)
            + "; at .01: "
            + ", ".join(f"{row['0.01'][str(k)]:.6f}" for k in scorer.ALL_K)
        )
    lines.extend(["", "## Gates", ""])
    lines.extend(f"- {'PASS' if passed else 'FAIL'} — `{name}`" for name, passed in gates.items())
    (args.output / "SONOTACO_2025_LITERATURE_COMPARISON.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    if not all(gates.values()):
        raise SystemExit(verdict)


if __name__ == "__main__":
    main()
