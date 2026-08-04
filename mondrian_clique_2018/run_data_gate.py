from __future__ import annotations

import bisect
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "mondrian_clique_2018"
OUTPUT = WORK_ROOT / "results" / "data_audit"
BASE_PARSER = ROOT / "real_shower_meta_stage0" / "audit_real_shower_data.py"
PROTOCOL = WORK_ROOT / "PROTOCOL.md"
EXPECTED_PARSER_BLOB = "4a029051230f7c6e99b09e911f8a9e5228a58783"
BLIND_LOW = 20.0
BLIND_HIGH = 55.0


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_parser() -> Path:
    actual_blob = subprocess.check_output(
        ["git", "hash-object", str(BASE_PARSER.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
    ).strip()
    if actual_blob != EXPECTED_PARSER_BLOB:
        raise RuntimeError(f"PR #14 parser blob mismatch: {actual_blob}")

    source = BASE_PARSER.read_text()
    replacements = {
        'OUT_DIR = ROOT / "results" / "data_audit"': 'OUT_DIR = Path("mondrian_clique_2018/results/data_audit")',
        'YEARS = (2019, 2021, 2023, 2025)': 'YEARS = (2018,)',
        '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] >= 3
            and profile["years_ge_20"] >= 3
        )''': '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] == 1
            and profile["years_ge_20"] == 1
        )''',
        'profile["strong"] = bool(profile["quality_events"] >= 1000 and profile["represented_years"] == 4)': 'profile["strong"] = bool(profile["quality_events"] >= 300 and profile["represented_years"] == 1)',
        '"strong_showers_at_least_12": len(strong) >= 12': '"strong_showers_at_least_8": len(strong) >= 8',
        '"multi_shower_complex_units_at_least_6": len(multi_shower_complexes) >= 6': '"multi_shower_complex_units_at_least_2": len(multi_shower_complexes) >= 2',
        '"quality_sporadics_at_least_200000": total_sporadic_quality >= 200_000': '"quality_sporadics_at_least_50000": total_sporadic_quality >= 50_000',
        'GhostStream was excluded. Data came from 48 official GMN monthly trajectory summaries and the IAU MDC shower file.': 'Fresh confirmation data came from 12 official 2018 GMN monthly trajectory summaries and the IAU MDC shower file.',
    }
    for old, new in replacements.items():
        count = source.count(old)
        if count != 1:
            raise RuntimeError(f"Expected one parser occurrence for replacement, got {count}: {old!r}")
        source = source.replace(old, new)

    derived = Path("/tmp/audit_2018_data.py")
    derived.write_text(source)
    subprocess.run([sys.executable, "-m", "py_compile", str(derived)], check=True, cwd=ROOT)
    return derived


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            events.append(event)
    return events


def calculate_coverage(events: list[dict[str, Any]], sources: list[dict[str, Any]]) -> dict[str, Any]:
    all_events_2018 = bool(events) and all(int(event["year"]) == 2018 for event in events)
    sporadic_sols = sorted(
        float(event["sol"]) % 360.0
        for event in events
        if int(event["iau"]) == -1
        and not (BLIND_LOW <= float(event["sol"]) <= BLIND_HIGH)
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

    source_gate = (
        len(sources) == 12
        and {int(item["month"]) for item in sources} == set(range(1, 13))
        and all(int(item.get("bytes", 0)) > 0 for item in sources)
    )
    return {
        "year": 2018,
        "selected_events": len(events),
        "all_selected_events_2018": all_events_2018,
        "sporadics_after_blind": len(sporadic_sols),
        "blind_interval_degrees": [BLIND_LOW, BLIND_HIGH],
        "supported_10deg_bins": supported,
        "supported_bin_count": len(supported),
        "maximum_local_count_by_bin": maximum_local_count,
        "gates": {
            "twelve_nonempty_monthly_sources": source_gate,
            "all_selected_events_are_2018": all_events_2018,
            "supported_10deg_bins_at_least_30": len(supported) >= 30,
        },
    }


def write_report(audit: dict[str, Any], coverage: dict[str, Any], gates: dict[str, bool]) -> None:
    verdict = "PASS_2018_DATA_GATE" if all(gates.values()) else "KILL_2018_DATA_GATE"
    result = {
        "verdict": verdict,
        "audit_counts": {
            "eligible_count": audit.get("eligible_count"),
            "strong_count": audit.get("strong_count"),
            "eligible_complex_units": audit.get("eligible_complex_units"),
            "total_quality_sporadics": audit.get("total_quality_sporadics"),
        },
        "audit_gates": audit.get("gates", {}),
        "coverage": coverage,
        "combined_gates": gates,
    }
    (OUTPUT / "data_gate_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Untouched 2018 data gate",
        "",
        f"Verdict: **`{verdict}`**",
        "",
        f"- eligible showers: **{audit.get('eligible_count')}**",
        f"- strong showers: **{audit.get('strong_count')}**",
        f"- eligible complex units: **{audit.get('eligible_complex_units')}**",
        f"- raw quality sporadics: **{audit.get('total_quality_sporadics')}**",
        f"- selected events: **{coverage['selected_events']}**",
        f"- post-blind sporadics: **{coverage['sporadics_after_blind']}**",
        f"- supported fixed 10° bins: **{coverage['supported_bin_count']}**",
        "",
        "## Gates",
        "",
    ]
    lines.extend(f"- `{name}`: **{passed}**" for name, passed in sorted(gates.items()))
    (OUTPUT / "DATA_GATE_REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


def write_provenance(derived: Path) -> None:
    tracked = [
        PROTOCOL,
        BASE_PARSER,
        derived,
        OUTPUT / "selected_events.jsonl.gz",
        OUTPUT / "audit.json",
        OUTPUT / "coverage.json",
        OUTPUT / "data_gate_result.json",
    ]
    lines = [f"{sha256_path(path)}  {path}" for path in tracked if path.exists()]
    (OUTPUT / "source_and_data_sha256.txt").write_text("\n".join(lines) + "\n")
    (OUTPUT / "base_source_blob_sha.txt").write_text(EXPECTED_PARSER_BLOB + "\n")
    (OUTPUT / "python_version.txt").write_text(sys.version + "\n")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    derived = derive_parser()
    subprocess.run([sys.executable, str(derived)], check=True, cwd=ROOT)

    audit_path = OUTPUT / "audit.json"
    events_path = OUTPUT / "selected_events.jsonl.gz"
    audit = json.loads(audit_path.read_text())
    if tuple(audit["configuration"]["years"]) != (2018,):
        raise RuntimeError(f"Unexpected audit years: {audit['configuration']['years']}")

    events = load_events(events_path)
    coverage = calculate_coverage(events, list(audit.get("sources", [])))
    (OUTPUT / "coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")

    audit_gates = {str(name): bool(value) for name, value in audit.get("gates", {}).items()}
    coverage_gates = {str(name): bool(value) for name, value in coverage["gates"].items()}
    gates = {**audit_gates, **coverage_gates}
    write_report(audit, coverage, gates)
    write_provenance(derived)

    if not all(gates.values()):
        raise SystemExit("Frozen untouched-2018 data gate failed")


if __name__ == "__main__":
    main()
