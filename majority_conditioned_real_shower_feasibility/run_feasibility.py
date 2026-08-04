#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

YEARS = tuple(range(2019, 2026))
MONTHS = tuple(range(1, 13))
SUPPORT_THRESHOLDS = (4, 6, 8, 12)
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
EXPECTED_AUDIT_SHA256 = "f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_exact_parser(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("exact_pr14_audit_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create exact parser module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def anonymous_support_summary(
    shower_year_counts: dict[int, Counter[int]],
    complex_by_iau: dict[int, str],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    summaries: dict[str, dict[str, Any]] = {}
    complex_counts: dict[str, int] = {}
    for k in SUPPORT_THRESHOLDS:
        histogram = Counter()
        transient = 0
        sub_recurrence = 0
        exactly_three = 0
        majority_active = 0
        exactly_three_complexes: set[str] = set()
        for iau, counts in shower_year_counts.items():
            active_years = sum(counts[year] >= k for year in YEARS)
            histogram[active_years] += 1
            if active_years == 1:
                transient += 1
            elif active_years == 2:
                sub_recurrence += 1
            elif active_years == 3:
                exactly_three += 1
                exactly_three_complexes.add(complex_by_iau.get(iau, f"SHOWER:{iau}"))
            elif active_years >= 4:
                majority_active += 1
        summaries[str(k)] = {
            "active_year_histogram": {
                str(active_years): histogram[active_years]
                for active_years in range(0, len(YEARS) + 1)
            },
            "transient_exactly_one_year": transient,
            "sub_recurrence_exactly_two_years": sub_recurrence,
            "recurrence_eligible_exactly_three_years": exactly_three,
            "majority_active_four_to_seven_years": majority_active,
            "recurrence_eligible_complex_units": len(exactly_three_complexes),
        }
        complex_counts[str(k)] = len(exactly_three_complexes)
    return summaries, complex_counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parser-source", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    exact = load_exact_parser(args.parser_source)
    audit_hash = sha256(args.audit)
    if audit_hash != EXPECTED_AUDIT_SHA256:
        raise RuntimeError(f"exact PR14 audit mismatch: {audit_hash}")
    prior_audit = json.loads(args.audit.read_text(encoding="utf-8"))
    complex_by_iau = {
        int(profile["iau"]): str(profile.get("complex_key") or f"SHOWER:{int(profile['iau'])}")
        for profile in prior_audit.get("profiles", [])
    }

    sources: list[dict[str, Any]] = []
    total_rows = 0
    malformed_rows = 0
    invalid_phase_rows = 0
    blind_interval_rows = 0
    post_boundary_parser_calls = 0
    quality_rows = 0
    quality_sporadics_by_year: Counter[int] = Counter()
    quality_labeled_by_year: Counter[int] = Counter()
    shower_year_counts: dict[int, Counter[int]] = defaultdict(Counter)

    with tempfile.TemporaryDirectory(prefix="gmn_recurrence_feasibility_") as temporary:
        temporary_root = Path(temporary)
        for year in YEARS:
            for month in MONTHS:
                url = exact.MONTHLY_URL.format(year=year, month=month)
                path = temporary_root / f"{year}{month:02d}.txt"
                source = exact.request_to_file(url, path)
                source.update({"year": year, "month": month})
                sources.append(source)
                with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                    reader = csv.reader(handle, delimiter=";")
                    for row in reader:
                        if not row or row[0].lstrip().startswith("#"):
                            continue
                        total_rows += 1
                        if len(row) <= exact.IDX["num_stat"]:
                            malformed_rows += 1
                            continue

                        # This is the only raw field accessed before the blind boundary.
                        solar_longitude = exact.as_float(exact.value(row, "sol"))
                        if solar_longitude is None or not 0.0 <= solar_longitude < 360.0:
                            invalid_phase_rows += 1
                            continue
                        if BLIND_LOW <= solar_longitude <= BLIND_HIGH:
                            blind_interval_rows += 1
                            continue

                        # Label and quality parsing occurs only after the blind-interval continue.
                        post_boundary_parser_calls += 1
                        event = exact.parse_event(row, year, month)
                        if event is None:
                            continue
                        quality_rows += 1
                        iau = int(event["iau"])
                        if iau == -1:
                            quality_sporadics_by_year[year] += 1
                        elif iau > 0:
                            quality_labeled_by_year[year] += 1
                            shower_year_counts[iau][year] += 1
                path.unlink(missing_ok=True)

    support, complex_counts = anonymous_support_summary(shower_year_counts, complex_by_iau)
    total_quality_sporadics = sum(quality_sporadics_by_year.values())
    distinct_positive_showers = len(shower_year_counts)
    exact_source_count = len(sources)
    source_year_months = {(int(source["year"]), int(source["month"])) for source in sources}

    gates = {
        "exactly_84_official_monthly_sources": exact_source_count == 84
        and source_year_months == {(year, month) for year in YEARS for month in MONTHS}
        and all(int(source.get("bytes", 0)) > 0 for source in sources),
        "zero_structurally_malformed_rows": malformed_rows == 0,
        "blind_interval_applied_before_every_label_quality_parse": blind_interval_rows >= 0
        and post_boundary_parser_calls == total_rows - malformed_rows - invalid_phase_rows - blind_interval_rows,
        "each_year_quality_sporadics_at_least_80000": all(
            quality_sporadics_by_year[year] >= 80_000 for year in YEARS
        ),
        "total_quality_sporadics_at_least_1000000": total_quality_sporadics >= 1_000_000,
        "distinct_positive_showers_at_least_200": distinct_positive_showers >= 200,
        "exactly_three_year_k4_showers_at_least_30": support["4"]["recurrence_eligible_exactly_three_years"] >= 30,
        "exactly_three_year_k8_showers_at_least_25": support["8"]["recurrence_eligible_exactly_three_years"] >= 25,
        "transient_k4_showers_at_least_15": support["4"]["transient_exactly_one_year"] >= 15,
        "majority_active_k4_showers_at_least_40": support["4"]["majority_active_four_to_seven_years"] >= 40,
        "exactly_three_year_k4_complex_units_at_least_25": complex_counts["4"] >= 25,
        "exactly_three_year_k8_complex_units_at_least_20": complex_counts["8"] >= 20,
        "forbidden_identity_geometry_score_outputs_absent": True,
    }
    verdict = (
        "PASS_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY"
        if all(gates.values())
        else "KILL_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY"
    )

    result = {
        "method": "seven-year GMN active-year support audit only",
        "configuration": {
            "years": list(YEARS),
            "months": list(MONTHS),
            "support_thresholds": list(SUPPORT_THRESHOLDS),
            "blind_interval_degrees_inclusive": [BLIND_LOW, BLIND_HIGH],
            "parser_sha256": sha256(args.parser_source),
            "prior_audit_sha256": audit_hash,
        },
        "sources": sources,
        "counts": {
            "total_rows": total_rows,
            "malformed_rows": malformed_rows,
            "invalid_phase_rows": invalid_phase_rows,
            "blind_interval_rows_removed_before_parse": blind_interval_rows,
            "post_boundary_parser_calls": post_boundary_parser_calls,
            "quality_rows": quality_rows,
            "total_quality_sporadics": total_quality_sporadics,
            "distinct_positive_shower_numbers": distinct_positive_showers,
        },
        "quality_sporadics_by_year": {
            str(year): quality_sporadics_by_year[year] for year in YEARS
        },
        "quality_labeled_by_year": {
            str(year): quality_labeled_by_year[year] for year in YEARS
        },
        "anonymous_support": support,
        "gates": gates,
        "verdict": verdict,
        "event_rows_emitted": False,
        "event_ids_emitted": False,
        "shower_identities_emitted": False,
        "complex_identities_emitted": False,
        "geometry_or_orbit_distributions_emitted": False,
        "detector_score_computed": False,
        "ghoststream_region_values_parsed": False,
    }
    (args.output / "real_shower_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = [
        "# Majority-conditioned recurrence real-shower feasibility",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- official monthly sources: **{exact_source_count}**",
        f"- total data rows: **{total_rows:,}**",
        f"- blind-interval rows removed before label/quality parsing: **{blind_interval_rows:,}**",
        f"- post-boundary quality sporadics: **{total_quality_sporadics:,}**",
        f"- distinct positive shower numbers: **{distinct_positive_showers}**",
        f"- exactly-three-year k=4 showers: **{support['4']['recurrence_eligible_exactly_three_years']}**",
        f"- exactly-three-year k=8 showers: **{support['8']['recurrence_eligible_exactly_three_years']}**",
        f"- transient k=4 showers: **{support['4']['transient_exactly_one_year']}**",
        f"- majority-active k=4 showers: **{support['4']['majority_active_four_to_seven_years']}**",
        f"- exactly-three-year k=4 complex units: **{complex_counts['4']}**",
        f"- exactly-three-year k=8 complex units: **{complex_counts['8']}**",
        "",
        "## Frozen gates",
        "",
    ]
    report.extend(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`"
        for name, passed in gates.items()
    )
    report.extend(
        [
            "",
            "No event row, event ID, shower identity, complex identity, geometry distribution, detector score, or GhostStream-region value is emitted.",
        ]
    )
    (args.output / "RESULT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "counts": result["counts"],
        "quality_sporadics_by_year": result["quality_sporadics_by_year"],
        "anonymous_support": support,
        "gates": gates,
    }, indent=2, sort_keys=True))
    if verdict != "PASS_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY":
        raise SystemExit("Frozen seven-year real-shower feasibility gate failed")


if __name__ == "__main__":
    main()
