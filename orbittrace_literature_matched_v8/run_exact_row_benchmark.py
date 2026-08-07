#!/usr/bin/env python3
"""Exact-event-row v8 vs HDBSCAN/Sugar pairwise benchmark.

The frozen competitor assignment artifacts define the event-row universes.  Shower labels
are not read until both v8 panel scans, family graphs, pooled centroids, scores and rankings
have been frozen.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_literature_matched_v8 import run_matched_benchmark as broad

v8 = broad.v8
YEARS = (2023, 2025)
MEMBERS = {2023: "023a/_U2_20230101_S.csv", 2025: "025a/_U2_20250101_S.csv"}
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
ASSIGNMENT_SHA256 = {
    "hdbscan": {
        2023: "7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60",
        2025: "8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3",
    },
    "sugar": {
        2023: "2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389",
        2025: "77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e",
    },
}
ARCHIVE_SHA256 = broad.ARCHIVE_SHA256
MAPPING_AUDIT_SHA256 = broad.MAPPING_AUDIT_SHA256
RAW_FIXED4_RANKING_VARIANTS = broad.RAW_FIXED4_RANKING_VARIANTS
MIN_SCAN_EVENTS = 1000


def args_parser() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--support-source-parts", required=True, type=Path)
    p.add_argument("--candidate-payload", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--scorer-parts", required=True, type=Path)
    p.add_argument("--parser-2023", required=True, type=Path)
    p.add_argument("--parser-2025", required=True, type=Path)
    p.add_argument("--mapping-audit", required=True, type=Path)
    p.add_argument("--archive-2023", required=True, type=Path)
    p.add_argument("--archive-2025", required=True, type=Path)
    p.add_argument("--hdbscan-2023", required=True, type=Path)
    p.add_argument("--hdbscan-2025", required=True, type=Path)
    p.add_argument("--sugar-2023", required=True, type=Path)
    p.add_argument("--sugar-2025", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm_header(x: str) -> str:
    return "".join(ch.lower() for ch in x.strip().lstrip("\ufeff") if ch.isalnum())


def load_hdbscan(path: Path, year: int) -> dict[str, int]:
    require(sha256_file(path) == ASSIGNMENT_SHA256["hdbscan"][year], f"HDBSCAN {year} assignment hash changed")
    lines = gzip.decompress(path.read_bytes()).decode("utf-8").splitlines()
    out: dict[str, int] = {}
    for line in lines:
        row = json.loads(line)
        event_id = str(row.get("event_id", row.get("id")))
        cluster = int(row.get("hdbscan_cluster", row.get("cluster")))
        require(event_id.startswith(f"SNM{year}:"), f"unexpected HDBSCAN id {event_id}")
        require(event_id not in out, f"duplicate HDBSCAN id {event_id}")
        out[event_id] = cluster
    require(len(out) == len(lines), f"HDBSCAN {year} duplicate rows")
    return out


def load_sugar(path: Path, year: int) -> dict[str, int]:
    require(sha256_file(path) == ASSIGNMENT_SHA256["sugar"][year], f"Sugar {year} assignment hash changed")
    payload = json.loads(gzip.decompress(path.read_bytes()))
    ids = [str(x) for x in payload["event_ids"]]
    labels = [int(x) for x in payload["retained_labels"]]
    require(len(ids) == len(labels), f"Sugar {year} assignment length mismatch")
    out: dict[str, int] = {}
    for event_id, cluster in zip(ids, labels):
        require(event_id.startswith(f"SNM{year}:"), f"unexpected Sugar id {event_id}")
        require(event_id not in out, f"duplicate Sugar id {event_id}")
        out[event_id] = cluster
    return out


def read_exact_geometry(year: int, archive: Path, requested: set[str], base: Any) -> list[dict[str, Any]]:
    require(len(requested) >= MIN_SCAN_EVENTS, f"too few exact rows for {year}: {len(requested)}")
    expected_prefix = f"SNM{year}:"
    row_indices: dict[int, str] = {}
    for event_id in requested:
        require(event_id.startswith(expected_prefix), f"wrong-year event id {event_id}")
        idx = int(event_id.split(":", 1)[1])
        require(idx >= 0 and idx not in row_indices, f"invalid/duplicate row index {event_id}")
        row_indices[idx] = event_id

    found: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(archive) as zf:
        require(MEMBERS[year] in zf.namelist(), f"missing archive member {MEMBERS[year]}")
        with zf.open(MEMBERS[year]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            reader = csv.reader(text)
            header = next(reader)
            while header and header[-1].strip() == "":
                header = header[:-1]
            names = [norm_header(x) for x in header]
            required_names = ("soldeg", "radeg", "dedeg", "vgkms")
            require(all(x in names for x in required_names), f"missing geometry headers in {year}: {names}")
            cols = {name: names.index(name) for name in required_names}
            width = len(header)
            for row_index, raw_row in enumerate(reader):
                if row_index not in row_indices:
                    continue
                row = list(raw_row)
                while len(row) > width and row[-1].strip() == "":
                    row.pop()
                require(len(row) >= width, f"short requested row {year}:{row_index}")
                event_id = row_indices[row_index]
                try:
                    sol = float(row[cols["soldeg"]]) % 360.0
                    ra = float(row[cols["radeg"]]) % 360.0
                    dec = float(row[cols["dedeg"]])
                    vg = float(row[cols["vgkms"]])
                except Exception as exc:
                    raise RuntimeError(f"unparseable requested geometry {event_id}") from exc
                require(all(math.isfinite(x) for x in (sol, ra, dec, vg)), f"nonfinite requested geometry {event_id}")
                require(not (BLIND_LOW <= sol <= BLIND_HIGH), f"competitor exact-row universe enters excluded interval: {event_id}")
                ecl_lon, ecl_lat = base.equatorial_to_ecliptic(ra, dec)
                found[event_id] = {
                    "id": event_id,
                    "year": year,
                    "sol": float(sol),
                    "sun_lon": float(base.wrap180(ecl_lon - sol)),
                    "ecl_lat": float(ecl_lat),
                    "vg": float(vg),
                    "iau": 0,
                    "complex_key": "HIDDEN",
                }
    missing = sorted(requested - set(found))
    require(not missing, f"requested competitor rows missing from raw geometry for {year}: {missing[:10]} (n={len(missing)})")
    require(len(found) == len(requested), f"exact-row geometry count mismatch {year}")
    return [found[event_id] for event_id in sorted(found, key=lambda x: int(x.split(":", 1)[1]))]


def parse_common_truth(parsers: dict[int, Any], archives: dict[int, Path], mapping_audit: Path, base: Any, panel_ids: dict[str, dict[int, set[str]]]) -> dict[str, dict[str, str]]:
    # This function is intentionally called only after every v8 panel ranking is frozen.
    mapped_by_year: dict[int, dict[str, str]] = {}
    for year in YEARS:
        function = getattr(parsers[year], f"parse_sonotaco_{year}_events")
        labeled, sporadic, audit = function(archives[year], mapping_audit, base)
        gates = broad.parser_gate_dict(audit)
        require(gates and all(gates.values()), f"common truth parser gates failed {year}")
        mapping: dict[str, str] = {}
        for event in labeled:
            event_id = str(event["id"])
            mapping[event_id] = str(event["complex_key"])
        for event in sporadic:
            mapping[str(event["id"])] = "SPORADIC"
        mapped_by_year[year] = mapping

    out: dict[str, dict[str, str]] = {}
    for panel, ids_by_year in panel_ids.items():
        truth: dict[str, str] = {}
        for year in YEARS:
            for event_id in ids_by_year[year]:
                truth[event_id] = mapped_by_year[year].get(event_id, "SPORADIC")
        out[panel] = truth
    return out


def summarize_match_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def one(subset: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "showers": len(subset),
            "mean_f1": float(np.mean([r["f1"] for r in subset])) if subset else None,
            "mean_precision": float(np.mean([r["precision"] for r in subset])) if subset else None,
            "mean_recall": float(np.mean([r["recall"] for r in subset])) if subset else None,
            "f1_gt_0_5": sum(float(r["f1"]) > 0.5 for r in subset),
            "f1_gt_0_8": sum(float(r["f1"]) > 0.8 for r in subset),
        }
    out = {"all": one(rows)}
    for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+"):
        out[bin_name] = one([r for r in rows if r["size_bin"] == bin_name])
    return out


def best_competitor_matches(assignments: dict[str, int], truth: dict[str, str], year: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ids = [event_id for event_id in assignments if event_id.startswith(f"SNM{year}:")]
    counts = Counter(truth[event_id] for event_id in ids if truth[event_id] != "SPORADIC")
    clusters: dict[int, list[str]] = defaultdict(list)
    for event_id in ids:
        cluster = int(assignments[event_id])
        if cluster >= 0:
            clusters[cluster].append(event_id)
    rows: list[dict[str, Any]] = []
    for label, actual in sorted(counts.items()):
        if actual < 4:
            continue
        best: tuple[float, float, int, int, float] | None = None
        for cluster, members in clusters.items():
            overlap = sum(truth[event_id] == label for event_id in members)
            precision, recall, f1 = broad.prf(overlap, len(members), int(actual))
            candidate = (f1, precision, overlap, -cluster, recall)
            if best is None or candidate > best:
                best = candidate
        if best is None:
            f1 = precision = recall = 0.0
            overlap = 0
            cluster_id = None
        else:
            f1, precision, overlap, neg_cluster, recall = best
            cluster_id = -neg_cluster
        rows.append({
            "label": label,
            "annual_members": int(actual),
            "size_bin": broad.size_bin(int(actual)),
            "cluster_id": cluster_id,
            "overlap": int(overlap),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        })
    return rows, summarize_match_rows(rows)


def v8_annual_with_richer_summary(families: list[dict[str, Any]], truth: dict[str, str], years: dict[str, int]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    rows_by_year, _ = broad.best_annual_matches(families, truth, years)
    return rows_by_year, {str(year): summarize_match_rows(rows_by_year[str(year)]) for year in YEARS}


def burden_for_families(families: list[dict[str, Any]], truth: dict[str, str]) -> dict[str, Any]:
    precisions: list[float] = []
    for family in families:
        members = [str(x) for x in family["event_ids"]]
        c = Counter(truth[event_id] for event_id in members)
        c.pop("SPORADIC", None)
        dominant = c.most_common(1)[0][1] if c else 0
        precisions.append(dominant / len(members) if members else 0.0)
    return {
        "returned_families": len(families),
        "dominant_known_precision_ge_0_5_fraction": float(np.mean([p >= 0.5 for p in precisions])) if precisions else 0.0,
        "mean_dominant_known_precision": float(np.mean(precisions)) if precisions else 0.0,
    }


def burden_for_clusters(assignments: dict[str, int], truth: dict[str, str]) -> dict[str, Any]:
    clusters: dict[int, list[str]] = defaultdict(list)
    noise = 0
    for event_id, cluster in assignments.items():
        if cluster < 0:
            noise += 1
        else:
            clusters[int(cluster)].append(event_id)
    precisions: list[float] = []
    for members in clusters.values():
        c = Counter(truth[event_id] for event_id in members)
        c.pop("SPORADIC", None)
        dominant = c.most_common(1)[0][1] if c else 0
        precisions.append(dominant / len(members) if members else 0.0)
    return {
        "returned_clusters": len(clusters),
        "noise_fraction": noise / len(assignments) if assignments else 0.0,
        "dominant_known_precision_ge_0_5_fraction": float(np.mean([p >= 0.5 for p in precisions])) if precisions else 0.0,
        "mean_dominant_known_precision": float(np.mean(precisions)) if precisions else 0.0,
    }


def run_v8_panel(name: str, scan_by_year: dict[int, list[dict[str, Any]]], support: Any, runtime: Any, base: Any) -> dict[str, Any]:
    start = time.perf_counter()
    components: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    quartets: dict[str, int] = {}
    for year in YEARS:
        audit, passing, year_components = v8.v6.label_free_scan_year(year, scan_by_year[year], support, base)
        require(audit["source_labels_used_for_proposals"] is False, f"{name} labels entered proposals {year}")
        require(audit["score_threshold_applied"] is False, f"{name} threshold entered proposals {year}")
        audits.append(audit)
        quartets[str(year)] = len(passing)
        components.extend(year_components)
        print(f"{name} exact-row v8 {year}: rows={len(scan_by_year[year])} quartets={len(passing)} components={len(year_components)}", flush=True)
    families, support_rankings = support.build_families(components, base)
    repair = v8.repair_year_centroids(families, components, scan_by_year, support, base)
    scored, scoring_summary = v8.mult.score_families(families, scan_by_year, runtime, base)
    multiplicity_order = v8.mult.rank_scored(scored, "multiplicity")
    require(set(multiplicity_order) == {str(f["family_id"]) for f in families}, f"{name} ranking universe mismatch")
    return {
        "families": families,
        "multiplicity_order": multiplicity_order,
        "support_rankings": support_rankings,
        "repair": repair,
        "scoring_summary": scoring_summary,
        "scan_audits": audits,
        "quartets": quartets,
        "components": len(components),
        "runtime_seconds": float(time.perf_counter() - start),
    }


def compare_summaries(v8_summary: dict[str, Any], comp_summary: dict[str, Any]) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    bins = ("4-9", "10-24", "25-49", "50-99", "100+", "all")
    for year in YEARS:
        y = str(year)
        comparison[y] = {}
        for bin_name in bins:
            vv = v8_summary[y][bin_name]
            cc = comp_summary[y][bin_name]
            require(vv["showers"] == cc["showers"], f"evaluation denominator mismatch {y} {bin_name}")
            vf = vv["mean_f1"]
            cf = cc["mean_f1"]
            delta = None if vf is None or cf is None else float(vf - cf)
            comparison[y][bin_name] = {
                "showers": vv["showers"],
                "v8": vv,
                "competitor": cc,
                "delta_mean_f1_v8_minus_competitor": delta,
                "material_v8_advantage_ge_0_10": bool(delta is not None and delta >= 0.10),
                "material_competitor_advantage_ge_0_10": bool(delta is not None and delta <= -0.10),
            }
    four_nine = all(comparison[str(y)]["4-9"]["material_v8_advantage_ge_0_10"] for y in YEARS)
    broad_sparse = four_nine and all(comparison[str(y)]["10-24"]["material_v8_advantage_ge_0_10"] for y in YEARS)
    return {
        "by_year_and_bin": comparison,
        "preregistered_gate_v8_beats_4_9_both_years": four_nine,
        "preregistered_gate_v8_beats_4_24_both_years": broad_sparse,
    }


def main() -> int:
    args = args_parser()
    args.output.mkdir(parents=True, exist_ok=True)
    require(sha256_file(args.mapping_audit) == MAPPING_AUDIT_SHA256, "mapping audit hash changed")
    archives = {2023: args.archive_2023, 2025: args.archive_2025}
    for year in YEARS:
        require(sha256_file(archives[year]) == ARCHIVE_SHA256[year], f"archive hash changed {year}")

    assignments = {
        "hdbscan": {
            2023: load_hdbscan(args.hdbscan_2023, 2023),
            2025: load_hdbscan(args.hdbscan_2025, 2025),
        },
        "sugar": {
            2023: load_sugar(args.sugar_2023, 2023),
            2025: load_sugar(args.sugar_2025, 2025),
        },
    }

    require(all(v8.mult.v3.self_test().values()), "v3 self-test failed")
    require(all(v8.mult.brown.self_test().values()), "Brown self-test failed")
    runtime = v8.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    require(float(support.BLIND_LOW) == BLIND_LOW and float(support.BLIND_HIGH) == BLIND_HIGH, "support blind interval changed")
    require(abs(float(support.FAMILY_LINK_RADIUS) - 1.5) <= 1e-15, "family link radius changed")
    require(int(support.MIN_COMPONENT_EVENTS) == 4 and int(support.MIN_COMPONENT_QUARTETS) == 2, "component gates changed")
    support.YEARS = YEARS
    support.MONTH_KEYS = tuple()
    support.CORPUS = "sonotaco-exact-row-literature-pairwise"
    support.RANKING_VARIANTS = RAW_FIXED4_RANKING_VARIANTS
    _candidate, base, _scorer = support.load_sources(args)

    v8.YEARS = YEARS
    v8.MONTH_KEYS = tuple()
    v8.mult.YEARS = YEARS
    v8.mult.MONTH_KEYS = tuple()

    panel_ids: dict[str, dict[int, set[str]]] = {
        panel: {year: set(assignments[panel][year]) for year in YEARS}
        for panel in ("hdbscan", "sugar")
    }
    scan_panels: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for panel in ("hdbscan", "sugar"):
        scan_panels[panel] = {
            year: read_exact_geometry(year, archives[year], panel_ids[panel][year], base)
            for year in YEARS
        }

    # Freeze both v8 pairwise outputs BEFORE loading any shower labels.
    v8_panels = {
        panel: run_v8_panel(panel, scan_panels[panel], support, runtime, base)
        for panel in ("hdbscan", "sugar")
    }

    parsers = {
        2023: load_module(args.parser_2023, "exact_row_truth_2023"),
        2025: load_module(args.parser_2025, "exact_row_truth_2025"),
    }
    truth_by_panel = parse_common_truth(parsers, archives, args.mapping_audit, base, panel_ids)

    results: dict[str, Any] = {}
    for panel in ("hdbscan", "sugar"):
        truth = truth_by_panel[panel]
        years = {event_id: int(event_id[3:7]) for event_id in truth}
        families = v8_panels[panel]["families"]
        v8_rows, v8_summary = v8_annual_with_richer_summary(families, truth, years)
        comp_rows_by_year: dict[str, Any] = {}
        comp_summary: dict[str, Any] = {}
        for year in YEARS:
            rows, summary = best_competitor_matches(assignments[panel][year], truth, year)
            comp_rows_by_year[str(year)] = rows
            comp_summary[str(year)] = summary
        comparison = compare_summaries(v8_summary, comp_summary)
        recurrent_rows, recurrent_summary = broad.best_recurrent_matches(families, truth, years)
        ranking = broad.ranking_metrics(families, v8_panels[panel]["multiplicity_order"], truth, years)
        results[panel] = {
            "exact_event_rows": {str(year): len(assignments[panel][year]) for year in YEARS},
            "v8_family_count": len(families),
            "v8_component_count": v8_panels[panel]["components"],
            "v8_retained_quartets": v8_panels[panel]["quartets"],
            "v8_runtime_seconds": v8_panels[panel]["runtime_seconds"],
            "v8_annual": v8_summary,
            "competitor_annual": comp_summary,
            "comparison": comparison,
            "v8_recurrent": recurrent_summary,
            "v8_ranking": {k: v for k, v in ranking.items() if k != "per_label"},
            "false_positive_burden": {
                "v8": burden_for_families(families, truth),
                "competitor": {str(year): burden_for_clusters(assignments[panel][year], truth) for year in YEARS},
            },
        }
        args.output.joinpath(f"exact_row_{panel}_v8_per_label.json").write_text(json.dumps(v8_rows, indent=2, sort_keys=True) + "\n")
        args.output.joinpath(f"exact_row_{panel}_competitor_per_label.json").write_text(json.dumps(comp_rows_by_year, indent=2, sort_keys=True) + "\n")
        args.output.joinpath(f"exact_row_{panel}_recurrent_per_label.json").write_text(json.dumps(recurrent_rows, indent=2, sort_keys=True) + "\n")

    integrity = {
        "exact_competitor_assignment_hashes": True,
        "exact_archive_hashes": True,
        "exact_mapping_audit_hash": True,
        "both_v8_panels_frozen_before_common_label_parse": True,
        "no_v8_parameter_change": True,
        "exact_row_counts_preserved": all(len(scan_panels[p][y]) == len(assignments[p][y]) for p in ("hdbscan", "sugar") for y in YEARS),
        "excluded_interval_absent_from_all_exact_rows": all(all(not (BLIND_LOW <= float(e["sol"]) <= BLIND_HIGH) for e in scan_panels[p][y]) for p in ("hdbscan", "sugar") for y in YEARS),
        "zero_source_labels_in_all_v8_proposals": all(all(a["source_labels_used_for_proposals"] is False for a in v8_panels[p]["scan_audits"]) for p in ("hdbscan", "sugar")),
        "no_score_threshold_in_all_v8_proposals": all(all(a["score_threshold_applied"] is False for a in v8_panels[p]["scan_audits"]) for p in ("hdbscan", "sugar")),
        "all_scored_episode_sizes_exact_128": all(v8_panels[p]["scoring_summary"]["episode_sizes"] == [128] if v8_panels[p]["families"] else True for p in ("hdbscan", "sugar")),
        "brown_equivalence_exact": all(float(v8_panels[p]["scoring_summary"]["max_brown_equivalence_difference"]) == 0.0 for p in ("hdbscan", "sugar")),
    }
    verdict = "PASS_V8_EXACT_ROW_PAIRWISE_LITERATURE_BENCHMARK" if all(integrity.values()) else "FAIL_V8_EXACT_ROW_PAIRWISE_INTEGRITY"
    out = {
        "verdict": verdict,
        "classification": "pairwise exact-event-row comparison of frozen v8 against frozen catalogue HDBSCAN and full Sugar retained-master assignments",
        "configuration": {
            "years": list(YEARS),
            "blind_exclusion": [BLIND_LOW, BLIND_HIGH],
            "v8_source_commit": "c9d6c44704013ba0c9430100e98a29a56b453304",
            "family_link_radius": 1.5,
            "episode_size": 128,
            "no_v8_parameter_change": True,
            "labels_loaded_only_after_both_pairwise_rankings_frozen": True,
            "unsupported_or_unmapped_native_tokens_common_truth": "SPORADIC",
            "material_delta_gate": 0.10,
        },
        "panels": results,
        "integrity_gates": integrity,
        "claim_boundary": "Exact rows and common mapped labels are identical within each pairwise comparator panel. HDBSCAN and Sugar remain annual catalogue methods while v8 proposals require cross-year recurrence, so the annual F1 comparison is a common recognition endpoint, not a claim that the algorithms solve identical optimization problems. CMOR remains deferred and D_SH remains an episode/targeted comparator. No OrbitTrace target information or excluded-interval contents were accessed.",
    }
    args.output.joinpath("v8_exact_row_pairwise.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    lines = [
        "# OrbitTrace v8 exact-event-row pairwise literature benchmark",
        "",
        f"**Verdict:** `{verdict}`",
        "",
    ]
    for panel in ("hdbscan", "sugar"):
        r = results[panel]
        lines += [
            f"## v8 vs {panel}",
            "",
            f"- exact rows: 2023={r['exact_event_rows']['2023']}, 2025={r['exact_event_rows']['2025']}",
            f"- v8 recurrent families: {r['v8_family_count']}",
            f"- v8 runtime: {r['v8_runtime_seconds']:.3f} s",
            f"- preregistered 4–9 win gate: **{r['comparison']['preregistered_gate_v8_beats_4_9_both_years']}**",
            f"- preregistered 4–24 win gate: **{r['comparison']['preregistered_gate_v8_beats_4_24_both_years']}**",
            "",
            "| Year | Bin | Showers | v8 mean F1 | competitor mean F1 | delta |",
            "|---:|:---|---:|---:|---:|---:|",
        ]
        for year in YEARS:
            for bin_name in ("4-9", "10-24", "25-49", "50-99", "100+", "all"):
                c = r["comparison"]["by_year_and_bin"][str(year)][bin_name]
                def fmt(x: Any) -> str:
                    return "n/a" if x is None else f"{float(x):.6f}"
                lines.append(f"| {year} | {bin_name} | {c['showers']} | {fmt(c['v8']['mean_f1'])} | {fmt(c['competitor']['mean_f1'])} | {fmt(c['delta_mean_f1_v8_minus_competitor'])} |")
        lines.append("")
    lines += [
        "No v8 parameter was changed. Both v8 panel rankings were frozen before the common shower-label parser was called.",
        "",
        "No OrbitTrace target information or excluded-interval contents were accessed.",
    ]
    args.output.joinpath("V8_EXACT_ROW_PAIRWISE.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
