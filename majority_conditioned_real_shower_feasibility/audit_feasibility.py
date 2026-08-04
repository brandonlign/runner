#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import gzip
import json
import math
from pathlib import Path

YEARS = (2019, 2021, 2023, 2025)
BLIND_LOW = 20.0
BLIND_HIGH = 55.0
THRESHOLDS = (4, 6, 8, 12, 20)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    if "profiles" not in audit:
        raise RuntimeError("frozen audit lacks profiles")

    total = 0
    blind_removed = 0
    background_years: collections.Counter[int] = collections.Counter()
    year_counts: collections.Counter[int] = collections.Counter()
    uncertainty_complete = 0
    shower_year_counts: collections.Counter[tuple[int, int]] = collections.Counter()
    complex_by_shower: dict[int, str] = {}
    first_fields: set[str] | None = None

    with gzip.open(args.events, "rt", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if first_fields is None:
                first_fields = set(event)
            solar = float(event["sol"]) % 360.0
            if BLIND_LOW <= solar <= BLIND_HIGH:
                blind_removed += 1
                continue
            total += 1
            year = int(event["year"])
            iau = int(event["iau"])
            year_counts[year] += 1
            sigmas = (event.get("ra_sigma"), event.get("dec_sigma"), event.get("vg_sigma"))
            if all(
                value is not None
                and math.isfinite(float(value))
                and float(value) >= 0.0
                for value in sigmas
            ):
                uncertainty_complete += 1
            if iau == -1:
                background_years[year] += 1
            else:
                shower_year_counts[(iau, year)] += 1
                key = str(event.get("complex_key", iau))
                prior = complex_by_shower.setdefault(iau, key)
                if prior != key:
                    raise RuntimeError(f"inconsistent complex key for shower {iau}")

    required = {
        "year", "sol", "ra", "dec", "vg", "iau", "complex_key",
        "ra_sigma", "dec_sigma", "vg_sigma",
    }
    if first_fields is None or not required.issubset(first_fields):
        raise RuntimeError("selected-event schema is incomplete")

    per_shower: dict[int, dict[int, int]] = collections.defaultdict(dict)
    for (iau, year), count in shower_year_counts.items():
        per_shower[iau][year] = count

    threshold_summary: dict[str, dict] = {}
    for threshold in THRESHOLDS:
        active = {
            iau: sum(count >= threshold for count in per_year.values())
            for iau, per_year in per_shower.items()
        }
        eligible = {iau: years for iau, years in active.items() if years >= 3}
        distribution = collections.Counter(eligible.values())
        threshold_summary[str(threshold)] = {
            "eligible_showers": len(eligible),
            "active_year_distribution": {
                str(key): value for key, value in sorted(distribution.items())
            },
            "eligible_complex_keys": len(
                {complex_by_shower[iau] for iau in eligible}
            ),
        }

    uncertainty_fraction = uncertainty_complete / total if total else 0.0
    gates = {
        "exact_retired_year_set": tuple(sorted(year_counts)) == YEARS,
        "background_at_least_10000_per_year": all(
            background_years[year] >= 10_000 for year in YEARS
        ),
        "uncertainty_completeness_at_least_0_99": uncertainty_fraction >= 0.99,
        "at_least_30_recurrent_showers": (
            threshold_summary["4"]["eligible_showers"] >= 30
        ),
        "no_confirmation_or_ghoststream_access": set(year_counts) == set(YEARS),
    }
    verdict = (
        "PASS_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY"
        if all(gates.values())
        else "KILL_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY"
    )
    result = {
        "method": "data-only majority-conditioned real-shower feasibility",
        "blind_interval": [BLIND_LOW, BLIND_HIGH],
        "counts": {
            "nonblind_events": total,
            "blind_rows_removed": blind_removed,
            "background_events": sum(background_years.values()),
            "uncertainty_complete": uncertainty_complete,
            "distinct_established_showers": len(per_shower),
        },
        "year_counts": dict(sorted(year_counts.items())),
        "background_year_counts": dict(sorted(background_years.items())),
        "uncertainty_completeness": uncertainty_fraction,
        "threshold_summary": threshold_summary,
        "gates": gates,
        "verdict": verdict,
        "event_rows_retained": False,
        "detector_scores_computed": False,
        "confirmation_data_read": False,
        "ghoststream_values_used": False,
    }
    (args.output / "real_shower_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (args.output / "RESULT.md").write_text(
        "# Majority-conditioned real-shower feasibility\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        f"- nonblind events: **{total:,}**\n"
        f"- background events: **{sum(background_years.values()):,}**\n"
        f"- k=4 recurrent showers: **{threshold_summary['4']['eligible_showers']}**\n"
        f"- uncertainty completeness: **{uncertainty_fraction:.6f}**\n\n"
        "No detector score or confirmation datum was read.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict != "PASS_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
