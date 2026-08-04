#!/usr/bin/env python3
"""Enforce the frozen 2018 extraction and fixed-bin coverage gates."""

from __future__ import annotations

import bisect
import gzip
import json
from pathlib import Path

ROOT = Path("mondrian_clique_2018/results/data_audit")


def main() -> None:
    audit = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
    if tuple(audit["configuration"]["years"]) != (2018,):
        raise RuntimeError(f"unexpected years: {audit['configuration']['years']}")
    if not all(audit["gates"].values()):
        raise SystemExit(f"frozen 2018 audit gates failed: {audit['gates']}")

    sources = audit.get("sources", [])
    source_gate = (
        len(sources) == 12
        and {int(item["month"]) for item in sources} == set(range(1, 13))
        and all(int(item.get("bytes", 0)) > 0 for item in sources)
    )

    events: list[dict] = []
    with gzip.open(ROOT / "selected_events.jsonl.gz", "rt", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            if int(event["year"]) != 2018:
                raise RuntimeError(f"unexpected event year: {event['year']}")
            events.append(event)

    sporadic_sols = sorted(
        float(event["sol"]) % 360.0
        for event in events
        if int(event["iau"]) == -1
        and not (20.0 <= float(event["sol"]) <= 55.0)
    )
    extended = (
        [value - 360.0 for value in sporadic_sols]
        + sporadic_sols
        + [value + 360.0 for value in sporadic_sols]
    )

    supported: list[int] = []
    maximum_local_count: dict[str, int] = {}
    for phase_bin in range(36):
        centers = [value for value in sporadic_sols if int(value // 10.0) == phase_bin]
        best = 0
        for center in centers:
            count = bisect.bisect_right(extended, center + 10.0) - bisect.bisect_left(
                extended, center - 10.0
            )
            best = max(best, count)
        maximum_local_count[str(phase_bin)] = best
        if best >= 128:
            supported.append(phase_bin)

    coverage = {
        "year": 2018,
        "selected_events": len(events),
        "sporadics_after_blind": len(sporadic_sols),
        "supported_10deg_bins": supported,
        "supported_bin_count": len(supported),
        "maximum_local_count_by_bin": maximum_local_count,
        "gates": {
            "twelve_nonempty_monthly_sources": source_gate,
            "supported_10deg_bins_at_least_30": len(supported) >= 30,
        },
    }
    (ROOT / "coverage.json").write_text(
        json.dumps(coverage, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "eligible_count": audit["eligible_count"],
                "strong_count": audit["strong_count"],
                "eligible_complex_units": audit["eligible_complex_units"],
                "total_quality_sporadics": audit["total_quality_sporadics"],
                "audit_gates": audit["gates"],
                "coverage": coverage,
            },
            indent=2,
        )
    )
    if not all(coverage["gates"].values()):
        raise SystemExit(f"frozen 2018 coverage gates failed: {coverage['gates']}")


if __name__ == "__main__":
    main()
