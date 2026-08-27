from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import run_static_matching as base
import run_static_matching_corrected  # noqa: F401  # applies clone-ready loader


_original_candidate_builder = base.candidate_groups_for_target
_original_match_candidate = base.match_candidate
_current_context: list[tuple[int, int]] = []
_stats: dict[tuple[int, int], dict[str, Any]] = defaultdict(
    lambda: {
        "total": 0,
        "individual_pass_counts": Counter(),
        "joint_pass_counts": Counter(),
        "best_score": math.inf,
        "best_diagnostics": None,
        "near_misses": [],
    }
)


def diagnostic_match(
    target: dict[str, Any], candidate: dict[str, Any]
) -> tuple[bool, dict[str, float]]:
    passed, diagnostics = _original_match_candidate(target, candidate)
    if not _current_context:
        return passed, diagnostics
    context = _current_context[-1]
    record = _stats[context]
    record["total"] += 1

    median_tolerance = max(0.002, 0.10 * target["d_median"])
    q90_tolerance = max(0.003, 0.15 * target["d_q90"])
    tests = {
        "orbit": diagnostics["orbit_distance"] <= base.ORBIT_TOL,
        "uncertainty": diagnostics["uncertainty_distance"] <= base.UNCERTAINTY_TOL,
        "d_median": diagnostics["d_median_abs_error"] <= median_tolerance,
        "d_q90": diagnostics["d_q90_abs_error"] <= q90_tolerance,
    }
    for name, result in tests.items():
        if result:
            record["individual_pass_counts"][name] += 1
    passed_names = tuple(sorted(name for name, result in tests.items() if result))
    record["joint_pass_counts"]["+".join(passed_names) or "none"] += 1

    score = float(diagnostics["score"])
    if score < record["best_score"]:
        record["best_score"] = score
        record["best_diagnostics"] = dict(diagnostics)
    near_miss = {
        **diagnostics,
        "passed_constraints": list(passed_names),
    }
    record["near_misses"].append(near_miss)
    record["near_misses"].sort(key=lambda item: item["score"])
    del record["near_misses"][20:]
    return passed, diagnostics


def diagnostic_builder(*args: Any, **kwargs: Any):
    control = int(args[-2])
    subgroup_index = int(args[-1])
    _current_context.append((control, subgroup_index))
    try:
        return _original_candidate_builder(*args, **kwargs)
    finally:
        _current_context.pop()


base.match_candidate = diagnostic_match
base.candidate_groups_for_target = diagnostic_builder


def output_directory() -> Path:
    try:
        index = sys.argv.index("--output")
    except ValueError as exc:
        raise RuntimeError("Missing --output") from exc
    return Path(sys.argv[index + 1])


if __name__ == "__main__":
    base.main()
    output = output_directory()
    payload: dict[str, Any] = {"subgroups": []}
    for (control, subgroup_index), record in sorted(_stats.items()):
        total = int(record["total"])
        payload["subgroups"].append(
            {
                "control": control,
                "subgroup_index": subgroup_index,
                "total_candidates_evaluated": total,
                "individual_pass_counts": dict(record["individual_pass_counts"]),
                "individual_pass_fractions": {
                    name: count / total if total else 0.0
                    for name, count in record["individual_pass_counts"].items()
                },
                "joint_pass_counts": dict(record["joint_pass_counts"]),
                "best_score": record["best_score"],
                "best_diagnostics": record["best_diagnostics"],
                "twenty_best_near_misses": record["near_misses"],
            }
        )
    (output / "constraint_diagnostic.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    aggregate_total = sum(item["total_candidates_evaluated"] for item in payload["subgroups"])
    aggregate_passes: Counter[str] = Counter()
    for item in payload["subgroups"]:
        aggregate_passes.update(item["individual_pass_counts"])
    lines = [
        "# Static matching constraint diagnostic",
        "",
        "This reruns the frozen candidate construction and tolerances unchanged.",
        "It records why candidates failed; it does not rescue the method.",
        "",
        f"Total candidate groups evaluated: **{aggregate_total:,}**",
        "",
        "| Constraint | Candidates passing alone | Fraction |",
        "|---|---:|---:|",
    ]
    for name in ("orbit", "uncertainty", "d_median", "d_q90"):
        count = aggregate_passes[name]
        fraction = count / aggregate_total if aggregate_total else 0.0
        lines.append(f"| {name} | {count:,} | {fraction:.6f} |")
    lines.extend(
        [
            "",
            "The authoritative static-matching verdict remains the frozen all-constraints result.",
        ]
    )
    report = "\n".join(lines)
    (output / "CONSTRAINT_DIAGNOSTIC_REPORT.md").write_text(report, encoding="utf-8")
    print(report)
