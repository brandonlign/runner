#!/usr/bin/env python3
"""Fresh target-excluded SonotaCo 2015/2017 validation of multiplicity ranking."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import requests
from scipy.stats import spearmanr

import run_holdout as v5

YEARS = (2015, 2017)
CORPUS = "sonotaco-2015-2017-sparse-support-multiplicity-external"
ARCHIVE_URLS = {
    2015: "https://sonotaco.jp/doc/SNMv3/015a.zip",
    2017: "https://sonotaco.jp/doc/SNMv3/017a.zip",
}
EXPECTED_MEMBERS = {
    2015: "015a/_U2_20150101_S.csv",
    2017: "017a/_U2_20170101_S.csv",
}
PARSER_SHA256 = {
    2015: "88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3",
    2017: "bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3",
}
MAPPING_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"
SUPPORT_SOURCE_SHA256 = "fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62"
RUNTIME_SOURCE_SHA256 = "ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51"
RAW_FIXED4_RANKING_VARIANTS = (
    "persistence",
    "mean_year_strength",
    "sqrt_support_strength",
    "min_year_strength",
    "size_penalized_strength",
)
RUNTIME_WRAPPER_YEARS = (2022, 2023)
RUNTIME_WRAPPER_CORPUS = "gmn-wavelet-catalogue-v3-development-2022-2023-excluding-sol20-55"
RUNTIME_WRAPPER_RANKINGS = ("wavelet_recurrence",)
BROWN_EQ_TOL = 1e-10
MIN_SUPPORTED_BINS = 24
MIN_SCAN_EVENTS = 1000
MIN_CALIBRATION_EVENTS = 1000
MIN_QUALIFIED = 30
MIN_HEAD = 30
MIN_TAIL = 30
DEVELOPMENT_FAMILIES = 197
DEVELOPMENT_TOP_K = 100


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2015", required=True, type=Path)
    p.add_argument("--parser-2017", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_frozen_scanner(args: argparse.Namespace) -> tuple[Any, Any, Any, Any, Any]:
    runtime = v5.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)

    require(tuple(support.YEARS) == RUNTIME_WRAPPER_YEARS, "unexpected runtime-presented support years")
    require(str(support.CORPUS) == RUNTIME_WRAPPER_CORPUS, "unexpected runtime-presented support corpus")
    require(tuple(support.RANKING_VARIANTS) == RUNTIME_WRAPPER_RANKINGS, "unexpected runtime-presented support ranking variants")
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "fixed blind interval changed")

    frozen = {
        "calibration": int(support.CALIBRATION_PER_BIN),
        "shortlist": int(support.SHORTLIST_K),
        "audit_shortlist": int(support.AUDIT_SHORTLIST_K),
        "min_anchor_count": int(support.MIN_ANCHOR_COUNT),
        "max_quartets_per_bin": int(support.MAX_QUARTETS_PER_BIN),
        "min_component_events": int(support.MIN_COMPONENT_EVENTS),
        "min_component_quartets": int(support.MIN_COMPONENT_QUARTETS),
        "min_family_years": int(support.MIN_FAMILY_YEARS),
        "family_link_radius": float(support.FAMILY_LINK_RADIUS),
    }
    expected = {
        "calibration": 128,
        "shortlist": 64,
        "audit_shortlist": 128,
        "min_anchor_count": 2,
        "max_quartets_per_bin": 512,
        "min_component_events": 4,
        "min_component_quartets": 2,
        "min_family_years": 2,
        "family_link_radius": 1.5,
    }
    require(frozen == expected, f"fixed4 scientific constants changed: {frozen}")

    # Preregistered survey transport only. No detector constant changes here.
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = RAW_FIXED4_RANKING_VARIANTS
    require(tuple(support.YEARS) == YEARS, "external year transport failed")
    require(str(support.CORPUS) == CORPUS, "external corpus transport failed")
    require(tuple(support.RANKING_VARIANTS) == RAW_FIXED4_RANKING_VARIANTS, "fixed4 ranking variants were not restored")

    candidate, base, scorer = support.load_sources(args)
    return runtime, support, candidate, base, scorer


def download_archive(year: int, directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    url = ARCHIVE_URLS[year]
    destination = directory / f"sonotaco_{year}.zip"
    response = requests.get(
        url,
        timeout=180,
        headers={"User-Agent": "OrbitTrace-target-free-validation/1.0"},
    )
    response.raise_for_status()
    payload = response.content
    require(len(payload) > 0, f"empty SonotaCo archive for {year}")
    destination.write_bytes(payload)
    return {
        "year": year,
        "url": url,
        "path": str(destination),
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def parser_gate_dict(audit: dict[str, Any]) -> dict[str, bool]:
    for key in ("gates", "parser_gates", "integrity_gates"):
        value = audit.get(key)
        if isinstance(value, dict):
            return {str(k): bool(v) for k, v in value.items()}
    raise RuntimeError("transported parser did not return a gate dictionary")


def parse_year(
    year: int,
    parser: Any,
    archive_path: Path,
    base: Any,
    mapping_audit: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    function = getattr(parser, f"parse_sonotaco_{year}_events")
    parsed = function(archive_path, base, mapping_audit)
    require(isinstance(parsed, tuple) and len(parsed) == 3, f"unexpected parser return for {year}")
    labeled, sporadic, audit = parsed
    require(isinstance(labeled, list) and isinstance(sporadic, list) and isinstance(audit, dict), f"unexpected parser payload for {year}")
    gates = parser_gate_dict(audit)
    require(gates and all(gates.values()), f"SonotaCo {year} parser integrity gates failed: {gates}")
    return labeled, sporadic, audit


def hidden_geometry(event: dict[str, Any], year: int, *, calibration: bool) -> dict[str, Any]:
    return {
        "id": str(event["id"]),
        "year": year,
        "sol": float(event["sol"]),
        "sun_lon": float(event["sun_lon"]),
        "ecl_lat": float(event["ecl_lat"]),
        "vg": float(event["vg"]),
        "iau": 0,
        "complex_key": "SPORADIC" if calibration else "HIDDEN",
    }


def build_hidden_panel(
    parsed_by_year: dict[int, tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]]
) -> tuple[dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]], dict[str, str], dict[str, int]]:
    scan_by_year: dict[int, list[dict[str, Any]]] = {}
    calibration_by_year: dict[int, list[dict[str, Any]]] = {}
    hidden_labels: dict[str, str] = {}
    hidden_years: dict[str, int] = {}
    seen: set[str] = set()

    for year in YEARS:
        labeled, sporadic, _audit = parsed_by_year[year]
        scan: list[dict[str, Any]] = []
        calibration: list[dict[str, Any]] = []

        for event in labeled:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate SonotaCo event ID: {event_id}")
            seen.add(event_id)
            label = str(event.get("complex_key", "")).strip()
            require(label and label != "SPORADIC", f"labeled parser event lacks mapped complex_key: {event_id}")
            hidden_labels[event_id] = label
            hidden_years[event_id] = year
            scan.append(hidden_geometry(event, year, calibration=False))

        for event in sporadic:
            event_id = str(event["id"])
            require(event_id not in seen, f"duplicate SonotaCo event ID: {event_id}")
            seen.add(event_id)
            hidden_labels[event_id] = "SPORADIC"
            hidden_years[event_id] = year
            geometry = hidden_geometry(event, year, calibration=False)
            scan.append(geometry)
            calibration.append(hidden_geometry(event, year, calibration=True))

        require(len(scan) >= MIN_SCAN_EVENTS, f"insufficient scan events for {year}: {len(scan)}")
        require(len(calibration) >= MIN_CALIBRATION_EVENTS, f"insufficient calibration events for {year}: {len(calibration)}")
        scan_by_year[year] = scan
        calibration_by_year[year] = calibration

    return scan_by_year, calibration_by_year, hidden_labels, hidden_years


def eligible_labels(hidden_labels: dict[str, str], hidden_years: dict[str, int]) -> dict[str, Counter[int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for event_id, label in hidden_labels.items():
        if label == "SPORADIC":
            continue
        year = int(hidden_years[event_id])
        if year in YEARS:
            counts[label][year] += 1
    return {
        label: per_year
        for label, per_year in counts.items()
        if sum(per_year.values()) >= 8 and all(per_year.get(year, 0) >= 4 for year in YEARS)
    }


def best_family_matches(
    hidden_labels: dict[str, str],
    hidden_years: dict[str, int],
    families: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any] | None], dict[str, Counter[int]]]:
    eligible = eligible_labels(hidden_labels, hidden_years)
    matches: dict[str, dict[str, Any] | None] = {}
    for label in sorted(eligible):
        total = int(sum(eligible[label].values()))
        candidates: list[tuple[float, float, int, str]] = []
        for family in families:
            overlap = sum(hidden_labels.get(str(event_id), "SPORADIC") == label for event_id in family["event_ids"])
            if overlap < 4:
                continue
            precision = overlap / int(family["event_count"])
            recall = overlap / total
            f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
            candidates.append((f1, precision, overlap, str(family["family_id"])))
        if not candidates:
            matches[label] = None
            continue
        f1, precision, overlap, family_id = max(candidates, key=lambda x: (x[0], x[1], x[2], x[3]))
        matches[label] = {
            "family_id": family_id,
            "overlap": int(overlap),
            "precision": float(precision),
            "recall": float(overlap / total),
            "f1": float(f1),
            "total": total,
        }
    return matches, eligible


def evaluate_order(
    order: list[str],
    families: list[dict[str, Any]],
    hidden_labels: dict[str, str],
    matches: dict[str, dict[str, Any] | None],
    eligible: dict[str, Counter[int]],
    k: int,
) -> dict[str, Any]:
    family_by_id = {str(f["family_id"]): f for f in families}
    require(len(order) == len(family_by_id) and set(order) == set(family_by_id), "ranking family universe mismatch")
    rank_map = {family_id: rank for rank, family_id in enumerate(order, 1)}

    dominant_precision: dict[str, float] = {}
    for family_id, family in family_by_id.items():
        counts = Counter(hidden_labels.get(str(event_id), "SPORADIC") for event_id in family["event_ids"])
        counts.pop("SPORADIC", None)
        dominant_count = counts.most_common(1)[0][1] if counts else 0
        dominant_precision[family_id] = dominant_count / int(family["event_count"]) if family["event_count"] else 0.0

    ranks: list[int] = []
    f1s: list[float] = []
    qualified = 0
    recovered = 0
    per_label: list[dict[str, Any]] = []
    qualified_labels: list[str] = []
    for label in sorted(eligible):
        match = matches[label]
        if match is None:
            per_label.append({"label": label, "rank": None, "qualified": False})
            continue
        rank = rank_map[str(match["family_id"])]
        is_qualified = bool(float(match["precision"]) >= 0.5 and int(match["overlap"]) >= 4)
        if is_qualified:
            qualified += 1
            recovered += int(rank <= k)
            ranks.append(rank)
            f1s.append(float(match["f1"]))
            qualified_labels.append(label)
        per_label.append({"label": label, "rank": rank, "qualified": is_qualified, **match})

    top = order[:k]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": qualified,
        "qualified_labels": qualified_labels,
        "recovered_at_k": recovered,
        "k": k,
        "mrr": float(np.mean([1.0 / rank for rank in ranks])) if ranks else 0.0,
        "median_rank": float(np.median(ranks)) if ranks else None,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "topk_dominant_precision": float(np.mean([dominant_precision[fid] for fid in top])) if top else 0.0,
        "per_label": per_label,
    }


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key not in {"per_label", "qualified_labels"}}


def rank_spearman(a: list[str], b: list[str]) -> float:
    require(set(a) == set(b), "rank-correlation family universe mismatch")
    universe = sorted(a)
    ra = {fid: i for i, fid in enumerate(a, 1)}
    rb = {fid: i for i, fid in enumerate(b, 1)}
    return float(spearmanr([ra[x] for x in universe], [rb[x] for x in universe]).statistic)


def topk_overlap(a: list[str], b: list[str], k: int) -> int:
    return len(set(a[:k]) & set(b[:k]))


def write_parser_integrity_failure(args: argparse.Namespace, stage: str, error: Exception, archive_sources: list[dict[str, Any]]) -> int:
    result = {
        "verdict": "FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_INTEGRITY",
        "stage": stage,
        "error_type": type(error).__name__,
        "error": str(error),
        "years": list(YEARS),
        "archive_sources": archive_sources,
        "blind_exclusion": [20.0, 55.0],
        "orbittrace_target_access": False,
        "scientific_ranking_result_available": False,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "multiplicity_sonotaco_external.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "MULTIPLICITY_SONOTACO_EXTERNAL.md").write_text(
        "# OrbitTrace SonotaCo 2015/2017 external validation\n\n"
        f"Verdict: **`{result['verdict']}`**\n\n"
        f"Integrity stage: `{stage}`. No scientific ranking verdict is available.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


def main() -> int:
    args = parse_args()
    args.archive_dir.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    # Every source/data-independent guard precedes the first archive request.
    require(sha256_file(args.parser_2015) == PARSER_SHA256[2015], "2015 parser hash changed")
    require(sha256_file(args.parser_2017) == PARSER_SHA256[2017], "2017 parser hash changed")
    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    require(all(v5.v3.self_test().values()), "frozen multi-anchor v3 self-test failed")
    require(all(v5.brown.self_test().values()), "frozen Brown comparator self-test failed")
    runtime, support, _candidate, base, scorer = load_frozen_scanner(args)
    parser_modules = {
        2015: load_module(args.parser_2015, "orbittrace_frozen_sonotaco_2015_parser"),
        2017: load_module(args.parser_2017, "orbittrace_frozen_sonotaco_2017_parser"),
    }
    for year, parser in parser_modules.items():
        require(int(parser.YEAR) == year, f"transported parser YEAR changed for {year}")
        require(str(parser.MEMBER) == EXPECTED_MEMBERS[year], f"transported parser member changed for {year}")
        require(float(parser.BLIND_SOLAR_MIN) == 20.0 and float(parser.BLIND_SOLAR_MAX) == 55.0, f"parser blind interval changed for {year}")
        require(parser.ARCHIVE_SHA256 is None and parser.MEMBER_SHA256 is None and parser.EXPECTED_ROWS is None, f"transported parser provenance placeholders changed for {year}")

    # FIRST ACCESS TO THE FRESH SONOTACO 2015/2017 ARCHIVES.
    archive_sources: list[dict[str, Any]] = []
    archives: dict[int, Path] = {}
    try:
        for year in YEARS:
            source = download_archive(year, args.archive_dir)
            archive_sources.append(source)
            archives[year] = Path(source["path"])
    except Exception as exc:
        return write_parser_integrity_failure(args, "archive_download", exc, archive_sources)

    try:
        parsed_by_year = {
            year: parse_year(year, parser_modules[year], archives[year], base, args.mapping_audit)
            for year in YEARS
        }
    except Exception as exc:
        return write_parser_integrity_failure(args, "parser_transport", exc, archive_sources)

    scan_by_year, calibration_by_year, hidden_labels, hidden_years = build_hidden_panel(parsed_by_year)

    # Proposals are target-free and label-free except that the frozen calibration
    # reservoir is restricted to parser-defined sporadics, exactly as preregistered.
    components: list[dict[str, Any]] = []
    scan_audits: list[dict[str, Any]] = []
    passing_counts: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = support.scan_year(
            year,
            scan_by_year[year],
            calibration_by_year[year],
            _candidate,
            base,
            scorer,
        )
        scan_audits.append(audit)
        passing_counts[str(year)] = len(passing)
        components.extend(year_components)
        print(f"SonotaCo {year}: fixed4 components={len(year_components)} retained_quartets={len(passing)}", flush=True)

    families, fixed_rankings = support.build_families(components, base)
    persistence_order = [str(fid) for fid in fixed_rankings["persistence"]]
    family_ids = [str(f["family_id"]) for f in families]
    require(len(persistence_order) == len(family_ids) and set(persistence_order) == set(family_ids), "fixed4 persistence ranking universe mismatch")

    # Reuse the exact v5 local-episode/scoring implementation with only the
    # preregistered external year tuple changed.
    v5.YEARS = YEARS
    scored, scoring_summary = v5.score_families(families, scan_by_year, runtime, base)
    multiplicity_order = v5.rank_scored(scored, "multiplicity")
    brown_order = v5.rank_scored(scored, "brown")
    v3_order = v5.rank_scored(scored, "v3")
    rankings = {
        "multiplicity": multiplicity_order,
        "brown": brown_order,
        "v3": v3_order,
        "fixed4_persistence": persistence_order,
    }
    universe = set(persistence_order)
    for name, order in rankings.items():
        require(len(order) == len(families) and set(order) == universe, f"{name} family universe mismatch")

    n_families = len(families)
    k = (DEVELOPMENT_TOP_K * n_families + DEVELOPMENT_FAMILIES - 1) // DEVELOPMENT_FAMILIES
    matches, eligible = best_family_matches(hidden_labels, hidden_years, families)
    metrics_full = {
        name: evaluate_order(order, families, hidden_labels, matches, eligible, k)
        for name, order in rankings.items()
    }
    metrics = {name: compact(value) for name, value in metrics_full.items()}

    qualified_sets = {
        name: tuple(metrics_full[name]["qualified_labels"])
        for name in rankings
    }
    identical_qualified = len(set(qualified_sets.values())) == 1
    qualified_count = int(metrics["multiplicity"]["qualified_matches"])

    parser_audits = {str(year): parsed_by_year[year][2] for year in YEARS}
    parser_gates_all = all(all(parser_gate_dict(parser_audits[str(year)]).values()) for year in YEARS)
    supported_bins_ok = all(len(audit["supported_bins"]) >= MIN_SUPPORTED_BINS for audit in scan_audits)
    exact_family_years = all(sorted(int(y) for y in family["years"]) == list(YEARS) for family in families)
    exact_episodes = (
        scoring_summary["episode_count"] == 2 * n_families
        and (scoring_summary["episode_sizes"] == [128] if n_families else True)
    )
    brown_equiv = float(scoring_summary["max_brown_equivalence_difference"]) <= BROWN_EQ_TOL
    ranking_power = bool(k >= MIN_HEAD and n_families - k >= MIN_TAIL)
    qualified_power = bool(qualified_count >= MIN_QUALIFIED)

    validity_gates = {
        "source_and_parser_prerequisite_guards": True,
        "exact_two_archive_urls_and_members": all(
            ARCHIVE_URLS[y] == next(s["url"] for s in archive_sources if s["year"] == y)
            and str(parser_modules[y].MEMBER) == EXPECTED_MEMBERS[y]
            for y in YEARS
        ),
        "both_parser_integrity_panels_pass": parser_gates_all,
        "blind_exclusion_before_labels_source_guarded": True,
        "at_least_1000_scan_and_calibration_events_each_year": all(
            len(scan_by_year[y]) >= MIN_SCAN_EVENTS and len(calibration_by_year[y]) >= MIN_CALIBRATION_EVENTS
            for y in YEARS
        ),
        "at_least_24_supported_fixed4_bins_each_year": supported_bins_ok,
        "all_recurrent_families_have_both_years": exact_family_years,
        "all_local_episode_sizes_exact_128": exact_episodes,
        "brown_equivalence_within_1e_10_everywhere": brown_equiv,
        "scaled_endpoint_has_at_least_30_head_and_30_tail": ranking_power,
        "at_least_30_qualified_known_showers": qualified_power,
        "identical_family_and_qualified_label_universes": identical_qualified,
    }

    m_recovery = int(metrics["multiplicity"]["recovered_at_k"])
    b_recovery = int(metrics["brown"]["recovered_at_k"])
    f_recovery = int(metrics["fixed4_persistence"]["recovered_at_k"])
    required_vs_fixed4 = int(math.ceil(0.90 * f_recovery))
    scientific_gates = {
        "multiplicity_recovers_at_least_one_more_than_brown_at_k": m_recovery >= b_recovery + 1,
        "multiplicity_recovers_at_least_90pct_of_fixed4_at_k": m_recovery >= required_vs_fixed4,
        "multiplicity_topk_precision_at_least_050": float(metrics["multiplicity"]["topk_dominant_precision"]) >= 0.50,
    }

    non_power_integrity = {
        key: value for key, value in validity_gates.items()
        if key not in {"scaled_endpoint_has_at_least_30_head_and_30_tail", "at_least_30_qualified_known_showers"}
    }
    if not all(non_power_integrity.values()):
        verdict = "FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_INTEGRITY"
    elif not ranking_power or not qualified_power:
        verdict = "INCONCLUSIVE_MULTIPLICITY_SONOTACO_EXTERNAL_POWER"
    elif all(scientific_gates.values()):
        verdict = "PASS_MULTIPLICITY_SONOTACO_EXTERNAL_VALIDATION"
    else:
        verdict = "FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_VALIDATION"

    correlations = {
        "multiplicity_brown_spearman": rank_spearman(multiplicity_order, brown_order),
        "multiplicity_v3_spearman": rank_spearman(multiplicity_order, v3_order),
        "multiplicity_fixed4_spearman": rank_spearman(multiplicity_order, persistence_order),
    }
    overlaps = {
        "multiplicity_brown_topk": topk_overlap(multiplicity_order, brown_order, k),
        "multiplicity_v3_topk": topk_overlap(multiplicity_order, v3_order, k),
        "multiplicity_fixed4_topk": topk_overlap(multiplicity_order, persistence_order, k),
    }

    result = {
        "verdict": verdict,
        "configuration": {
            "years": list(YEARS),
            "corpus": CORPUS,
            "blind_exclusion": [20.0, 55.0],
            "development_family_count": DEVELOPMENT_FAMILIES,
            "development_top_k": DEVELOPMENT_TOP_K,
            "scaled_k_formula": "ceil(100*N/197)",
            "k": k,
            "family_count": n_families,
            "primary_ranking": "min yearly multiplicity, geometric-mean multiplicity, family id",
            "multiplicity": "(multi-anchor-v3-energy / Brown-peak)^2",
            "no_multiplicity_pvalue": True,
            "no_rrf": True,
            "no_threshold_search": True,
            "no_weight_search": True,
            "no_endpoint_search": True,
        },
        "archive_sources": archive_sources,
        "parser_audits": parser_audits,
        "scan_event_counts": {str(y): len(scan_by_year[y]) for y in YEARS},
        "calibration_event_counts": {str(y): len(calibration_by_year[y]) for y in YEARS},
        "fixed4_scan_audits": scan_audits,
        "passing_quartet_counts": passing_counts,
        "family_scoring_summary": scoring_summary,
        "metrics": metrics,
        "correlations": correlations,
        "topk_overlaps": overlaps,
        "validity_gates": validity_gates,
        "scientific_gates": scientific_gates,
        "required_multiplicity_recovery_vs_fixed4": required_vs_fixed4,
        "claim_boundary": (
            "Fresh repo-history-unexposed SonotaCo 2015/2017 target-excluded external catalogue-ranking validation. "
            "The closed 20-55 degree interval was excluded before shower-label access. "
            "No OrbitTrace target coordinates, members, activity, identity, or consistency criterion were accessed. "
            "Even a PASS does not authorize target reveal; a separate final discovery-application protocol is required."
        ),
    }

    (args.output / "multiplicity_sonotaco_external.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.output / "multiplicity_sonotaco_external_rankings.json").write_text(json.dumps(rankings, indent=2) + "\n")
    (args.output / "multiplicity_sonotaco_external_evaluation.json").write_text(json.dumps(metrics_full, indent=2) + "\n")
    (args.output / "multiplicity_sonotaco_external_family_scores.json").write_text(json.dumps(scored, indent=2) + "\n")

    lines = [
        "# OrbitTrace multiplicity — fresh SonotaCo 2015/2017 external validation",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- recurrent families: **{n_families}**",
        f"- scaled endpoint K=ceil(100N/197): **{k}** (tail **{n_families-k}**)",
        f"- qualified known showers: **{qualified_count}**",
        f"- multiplicity recovered@K: **{m_recovery}**; precision@K **{metrics['multiplicity']['topk_dominant_precision']:.4f}**; MRR **{metrics['multiplicity']['mrr']:.6f}**; median rank **{metrics['multiplicity']['median_rank']}**",
        f"- Brown recovered@K: **{b_recovery}**; precision@K **{metrics['brown']['topk_dominant_precision']:.4f}**; MRR **{metrics['brown']['mrr']:.6f}**; median rank **{metrics['brown']['median_rank']}**",
        f"- total-v3 recovered@K: **{metrics['v3']['recovered_at_k']}**; precision@K **{metrics['v3']['topk_dominant_precision']:.4f}**",
        f"- fixed4 persistence recovered@K: **{f_recovery}**; precision@K **{metrics['fixed4_persistence']['topk_dominant_precision']:.4f}**",
        f"- required multiplicity recovery for 90% fixed4 gate: **{required_vs_fixed4}**",
        f"- multiplicity vs fixed4 rank Spearman: **{correlations['multiplicity_fixed4_spearman']:.4f}**",
        f"- maximum Brown-equivalence difference: **{scoring_summary['max_brown_equivalence_difference']:.3e}**",
        "",
        "The 20°–55° solar-longitude interval remained excluded before label access, and OrbitTrace remained blinded.",
    ]
    (args.output / "MULTIPLICITY_SONOTACO_EXTERNAL.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
