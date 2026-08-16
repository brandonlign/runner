#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from gmn_python_api import data_directory as dd

YEARS = (2022, 2023)
MONTHS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
EXPECTED = {
    (128, 0): 5567,
    (128, 1): 5840,
    (128, 2): 5857,
    (128, 3): 5816,
    (1024, 0): 677,
    (1024, 1): 739,
    (1024, 2): 736,
    (1024, 3): 766,
}
MIN_COMPLETE = 0.95


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def clean_header(x: str) -> str:
    return " ".join(x.replace("#", "").strip().split())


def selected_columns(text: str) -> tuple[int, int, int, list[str]]:
    lines = text.splitlines()
    top = next((ln for ln in lines if ln.lstrip().startswith("#") and "Unique trajectory" in ln and "Sol lon" in ln and "Participating" in ln), None)
    bottom = next((ln for ln in lines if ln.lstrip().startswith("#") and "identifier" in ln and "stat" in ln and "stations" in ln), None)
    req(top is not None and bottom is not None, "GMN monthly two-row schema header not found")
    a = [clean_header(x) for x in top.split(";")]
    b = [clean_header(x) for x in bottom.split(";")]
    req(len(a) == len(b) and len(a) > 70, f"unexpected GMN header width {len(a)} vs {len(b)}")

    def one(t: str, u: str) -> int:
        hits = [i for i, (x, y) in enumerate(zip(a, b)) if x == t and y == u]
        req(len(hits) == 1, f"header field {(t,u)} not unique: {hits}")
        return hits[0]

    return one("Unique trajectory", "identifier"), one("Sol lon", "deg"), one("Num", "stat"), lines


def parse_month(text: str, month: str) -> list[tuple[str, float, int | None]]:
    id_col, sol_col, stat_col, lines = selected_columns(text)
    out: list[tuple[str, float, int | None]] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        cells = [x.strip() for x in line.split(";")]
        req(max(id_col, sol_col, stat_col) < len(cells), f"short data row in {month}")
        eid = cells[id_col]
        req(re.fullmatch(r"[A-Za-z0-9_]+", eid) is not None, f"unsafe event id in {month}: {eid!r}")
        req(eid.startswith(month[:4]), f"event year mismatch {month}: {eid}")
        sol = float(cells[sol_col]) % 360.0
        req(math.isfinite(sol), f"nonfinite solar longitude for {eid}")
        raw = cells[stat_col]
        nstat: int | None = None
        if raw not in {"", "...", "nan", "NaN", "None"}:
            x = float(raw)
            if math.isfinite(x) and x.is_integer():
                nstat = int(x)
        out.append((eid, sol, nstat))
    req(out, f"no data rows parsed for {month}")
    return out


def h64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + eid).encode("utf-8")).digest()[:8], "big")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    rows: dict[str, tuple[int, int | None]] = {}
    raw_month_sha: dict[str, str] = {}
    all_hist = Counter()
    protected_numstat_values_emitted = False

    for month in MONTHS:
        print(f"[numstat] fetch {month}", flush=True)
        text = dd.get_monthly_file_content_by_date(month)
        raw_month_sha[month] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        parsed = parse_month(text, month)
        for eid, sol, nstat in parsed:
            if BLIND[0] <= sol <= BLIND[1]:
                # Critically, do not store or histogram this row's station count.
                continue
            req(eid not in rows, f"duplicate target-excluded trajectory ID {eid}")
            year = int(eid[:4])
            req(year in YEARS, f"unexpected year {year}")
            rows[eid] = (year, nstat)
            if nstat is not None and nstat >= 2:
                all_hist[nstat] += 1

    subset_ids: dict[tuple[int, int], list[str]] = {}
    for d in DENOMS:
        for b in BUCKETS:
            ids = sorted(eid for eid in rows if h64(eid) % d == b)
            req(len(ids) == EXPECTED[(d, b)], f"frozen subset count changed d={d} b={b}: {len(ids)} != {EXPECTED[(d,b)]}")
            subset_ids[(d, b)] = ids

    audited_union = sorted(set().union(*(set(v) for v in subset_ids.values())))
    # d1024 buckets are nested within same-bucket d128, so union is four d128 buckets.
    req(len(audited_union) == sum(EXPECTED[(128, b)] for b in BUCKETS), "audited-union nesting changed")

    def usable(eid: str) -> bool:
        n = rows[eid][1]
        return isinstance(n, int) and n >= 2

    year_stats = {}
    for y in YEARS:
        ids = [eid for eid in audited_union if rows[eid][0] == y]
        good = [eid for eid in ids if usable(eid)]
        frac = len(good) / len(ids) if ids else 0.0
        year_stats[str(y)] = {
            "requested": len(ids),
            "usable_integer_ge2": len(good),
            "complete_fraction": frac,
            "gate_at_least_0_95": bool(frac >= MIN_COMPLETE),
        }

    subset_stats = {}
    for d in DENOMS:
        for b in BUCKETS:
            ids = subset_ids[(d, b)]
            good = [eid for eid in ids if usable(eid)]
            frac = len(good) / len(ids)
            subset_stats[f"d{d}_b{b}"] = {
                "requested": len(ids),
                "usable_integer_ge2": len(good),
                "complete_fraction": frac,
                "gate_at_least_0_95": bool(frac >= MIN_COMPLETE),
                "all_events_usable": bool(len(good) == len(ids)),
            }

    sparse_hist = Counter(rows[eid][1] for eid in audited_union if usable(eid))
    mapping = {eid: (int(rows[eid][1]) if usable(eid) else None) for eid in audited_union}
    mapping_raw = (json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    mapping_sha = hashlib.sha256(mapping_raw).hexdigest()

    gates = {
        "exact_subset_counts": True,
        "year_2022_complete_ge_0_95": bool(year_stats["2022"]["gate_at_least_0_95"]),
        "year_2023_complete_ge_0_95": bool(year_stats["2023"]["gate_at_least_0_95"]),
        "all_eight_subsets_complete_ge_0_95": all(x["gate_at_least_0_95"] for x in subset_stats.values()),
        "protected_values_not_emitted": not protected_numstat_values_emitted,
    }
    verdict = "PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1" if all(gates.values()) else "FAIL_TOPOMODAL_NUMSTAT_AVAILABILITY_V1"

    result = {
        "schema": "ORBITTRACE_TOPOMODAL_NUMSTAT_AVAILABILITY_V1",
        "verdict": verdict,
        "years": list(YEARS),
        "blind_exclusion": list(BLIND),
        "minimum_complete_fraction": MIN_COMPLETE,
        "expected_subset_counts": {f"d{d}_b{b}": EXPECTED[(d, b)] for d in DENOMS for b in BUCKETS},
        "target_excluded_rows_total": len(rows),
        "audited_union_count": len(audited_union),
        "year_stats": year_stats,
        "subset_stats": subset_stats,
        "target_excluded_all_numstat_histogram_diagnostic_only": {str(k): int(v) for k, v in sorted(all_hist.items())},
        "audited_union_numstat_histogram_diagnostic_only": {str(k): int(v) for k, v in sorted(sparse_hist.items())},
        "audited_mapping_sha256": mapping_sha,
        "monthly_raw_sha256": raw_month_sha,
        "gates": gates,
        "source": "official_GMN_monthly_trajectory_files_via_gmn_python_api_0_0_13",
        "fields_parsed": ["unique_trajectory_identifier", "sol_lon_deg", "num_stat"],
        "station_codes_parsed": False,
        "station_geography_accessed": False,
        "participating_station_field_parsed": False,
        "shower_truth_parsed": False,
        "meteor_geometry_parsed": False,
        "target_information_access": False,
        "target_region_station_count_emitted_or_used": False,
        "sonotaco_scientific_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "scientific_ranking_computed": False,
        "post_result_parameter_search": False,
    }
    (args.output / "TOPOMODAL_NUMSTAT_AVAILABILITY_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (args.output / "audited_union_numstat_mapping.json").write_bytes(mapping_raw)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
