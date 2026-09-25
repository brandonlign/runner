from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import random
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("dynamical_coherence_stage0")
OUT_DIR = ROOT / "results" / "data_gate"
YEARS = (2019, 2021, 2023, 2025)
CONTROL_MONTH = {4: 12, 6: 4, 7: 8, 10: 1, 13: 11}
MONTHS = tuple(sorted(set(CONTROL_MONTH.values())))
CONTROL_NUMBERS = tuple(sorted(CONTROL_MONTH))
SPORADIC_NUMBER = -1
SPORADIC_RESERVOIR_PER_STRATUM = 5000
URL_TEMPLATE = "https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt"
USER_AGENT = "ghoststream-predictability-dynamics/1.0"

# Official GMN trajectory-summary positions.
IDX = {
    "id": 0,
    "jd": 1,
    "utc": 2,
    "iau": 3,
    "code": 4,
    "sol": 5,
    "a": 23,
    "a_sigma": 24,
    "e": 25,
    "e_sigma": 26,
    "i": 27,
    "i_sigma": 28,
    "peri": 29,
    "peri_sigma": 30,
    "node": 31,
    "node_sigma": 32,
    "q": 37,
    "q_sigma": 38,
    "f": 39,
    "f_sigma": 40,
    "M": 41,
    "M_sigma": 42,
    "Tj": 49,
    "Tj_sigma": 50,
    "Qc": 80,
    "fiterr": 81,
    "num_stat": 84,
}


def as_float(value: str | None) -> float | None:
    text = (value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "..."}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def as_int(value: str | None) -> int | None:
    number = as_float(value)
    if number is None or abs(number - round(number)) > 1e-8:
        return None
    return int(round(number))


def value(row: list[str], key: str) -> str | None:
    index = IDX[key]
    return row[index].strip() if index < len(row) else None


def parse_event(row: list[str], year: int, month: int) -> dict[str, Any] | None:
    shower = as_int(value(row, "iau"))
    if shower is None:
        shower = -1
    target_control = shower in CONTROL_NUMBERS and CONTROL_MONTH[shower] == month
    if not target_control and shower != SPORADIC_NUMBER:
        return None

    jd = as_float(value(row, "jd"))
    a = as_float(value(row, "a"))
    e = as_float(value(row, "e"))
    inc = as_float(value(row, "i"))
    peri = as_float(value(row, "peri"))
    node = as_float(value(row, "node"))
    q = as_float(value(row, "q"))
    true_anomaly = as_float(value(row, "f"))
    mean_anomaly = as_float(value(row, "M"))
    tj = as_float(value(row, "Tj"))
    qc = as_float(value(row, "Qc"))
    fiterr = as_float(value(row, "fiterr"))
    num_stat = as_int(value(row, "num_stat"))

    state_ok = bool(
        jd is not None
        and jd > 2_000_000
        and a is not None
        and 0.0 < a < 100.0
        and e is not None
        and 0.0 <= e < 1.2
        and inc is not None
        and 0.0 <= inc <= 180.0
        and peri is not None
        and 0.0 <= peri < 360.0
        and node is not None
        and 0.0 <= node < 360.0
        and q is not None
        and 0.0 < q < 1.3
        and (true_anomaly is not None or mean_anomaly is not None)
    )

    sigma_keys = ("a_sigma", "e_sigma", "i_sigma", "peri_sigma", "node_sigma")
    sigmas = {key: as_float(value(row, key)) for key in sigma_keys}
    f_sigma = as_float(value(row, "f_sigma"))
    m_sigma = as_float(value(row, "M_sigma"))
    anomaly_sigma = f_sigma if f_sigma is not None else m_sigma
    uncertainty_ok = bool(
        all(item is not None and item >= 0.0 for item in sigmas.values())
        and anomaly_sigma is not None
        and anomaly_sigma >= 0.0
    )
    quality_ok = bool(
        state_ok
        and (qc is None or qc >= 10.0)
        and (fiterr is None or fiterr <= 300.0)
        and (num_stat is None or num_stat >= 2)
    )

    return {
        "id": value(row, "id"),
        "utc": value(row, "utc"),
        "year": year,
        "month": month,
        "iau": shower,
        "code": value(row, "code"),
        "jd": jd,
        "sol": as_float(value(row, "sol")),
        "a": a,
        "e": e,
        "i": inc,
        "peri": peri,
        "node": node,
        "q": q,
        "f": true_anomaly,
        "M": mean_anomaly,
        "Tj": tj,
        "a_sigma": sigmas["a_sigma"],
        "e_sigma": sigmas["e_sigma"],
        "i_sigma": sigmas["i_sigma"],
        "peri_sigma": sigmas["peri_sigma"],
        "node_sigma": sigmas["node_sigma"],
        "f_sigma": f_sigma,
        "M_sigma": m_sigma,
        "Tj_sigma": as_float(value(row, "Tj_sigma")),
        "Qc": qc,
        "fiterr": fiterr,
        "num_stat": num_stat,
        "state_ok": state_ok,
        "uncertainty_ok": uncertainty_ok,
        "quality_ok": quality_ok,
    }


def download(url: str, destination: Path) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    sha256 = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(request, timeout=300) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)
            total += len(chunk)
            output.write(chunk)
    return {"url": url, "bytes": total, "sha256": sha256.hexdigest()}


def reservoir_add(
    reservoirs: dict[tuple[int, int], list[dict[str, Any]]],
    seen: Counter[tuple[int, int]],
    event: dict[str, Any],
    rngs: dict[tuple[int, int], random.Random],
) -> None:
    key = (event["year"], event["month"])
    seen[key] += 1
    bucket = reservoirs[key]
    if len(bucket) < SPORADIC_RESERVOIR_PER_STRATUM:
        bucket.append(event)
        return
    index = rngs[key].randrange(seen[key])
    if index < SPORADIC_RESERVOIR_PER_STRATUM:
        bucket[index] = event


def median(values: list[float]) -> float | None:
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return 0.5 * (values[middle - 1] + values[middle])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    control_events: list[dict[str, Any]] = []
    reservoirs: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    sporadic_seen: Counter[tuple[int, int]] = Counter()
    rngs = {
        (year, month): random.Random(20260803 + year * 100 + month)
        for year in YEARS
        for month in MONTHS
    }
    source_files: list[dict[str, Any]] = []
    selected_counts: Counter[int] = Counter()
    quality_counts: Counter[int] = Counter()
    state_counts: Counter[int] = Counter()
    uncertainty_counts: Counter[int] = Counter()
    control_year_counts: dict[int, Counter[int]] = defaultdict(Counter)
    malformed_rows = 0

    with tempfile.TemporaryDirectory(prefix="gmn_monthly_") as temp_directory:
        temp_root = Path(temp_directory)
        for year in YEARS:
            for month in MONTHS:
                url = URL_TEMPLATE.format(year=year, month=month)
                path = temp_root / f"{year}{month:02d}.txt"
                source = download(url, path)
                source.update({"year": year, "month": month})
                source_files.append(source)
                with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                    reader = csv.reader(handle, delimiter=";")
                    for row in reader:
                        if not row or row[0].lstrip().startswith("#"):
                            continue
                        if len(row) <= IDX["num_stat"]:
                            malformed_rows += 1
                            continue
                        event = parse_event(row, year, month)
                        if event is None:
                            continue
                        shower = int(event["iau"])
                        selected_counts[shower] += 1
                        state_counts[shower] += int(event["state_ok"])
                        uncertainty_counts[shower] += int(event["uncertainty_ok"])
                        if not event["quality_ok"]:
                            continue
                        quality_counts[shower] += 1
                        if shower == SPORADIC_NUMBER:
                            reservoir_add(reservoirs, sporadic_seen, event, rngs)
                        else:
                            control_year_counts[shower][year] += 1
                            control_events.append(event)
                path.unlink(missing_ok=True)

    sporadic_events = [event for key in sorted(reservoirs) for event in reservoirs[key]]
    all_saved = control_events + sporadic_events
    with gzip.open(OUT_DIR / "selected_events.jsonl.gz", "wt", encoding="utf-8") as output:
        for event in all_saved:
            output.write(json.dumps(event, sort_keys=True) + "\n")

    profiles: list[dict[str, Any]] = []
    for shower in (*CONTROL_NUMBERS, SPORADIC_NUMBER):
        controls = [event for event in control_events if event["iau"] == shower]
        profiles.append({
            "iau": shower,
            "code_counts": dict(Counter(event["code"] for event in controls)),
            "selected_rows": selected_counts[shower],
            "quality_rows": quality_counts[shower],
            "state_fraction": state_counts[shower] / selected_counts[shower] if selected_counts[shower] else 0.0,
            "uncertainty_fraction": uncertainty_counts[shower] / selected_counts[shower] if selected_counts[shower] else 0.0,
            "year_counts": {str(year): control_year_counts[shower][year] for year in YEARS} if shower != -1 else {f"{year}-{month:02d}": sporadic_seen[(year, month)] for year in YEARS for month in MONTHS},
            "median_a": median([float(event["a"]) for event in controls if event["a"] is not None]),
            "median_i": median([float(event["i"]) for event in controls if event["i"] is not None]),
            "median_Tj": median([float(event["Tj"]) for event in controls if event["Tj"] is not None]),
        })

    control_profiles = [profile for profile in profiles if profile["iau"] in CONTROL_NUMBERS]
    inclinations = [profile["median_i"] for profile in control_profiles if profile["median_i"] is not None]
    semimajor_axes = [profile["median_a"] for profile in control_profiles if profile["median_a"] is not None]
    tisserand = [profile["median_Tj"] for profile in control_profiles if profile["median_Tj"] is not None]
    selected_total = sum(selected_counts.values())
    state_total = sum(state_counts.values())
    uncertainty_total = sum(uncertainty_counts.values())

    gates = {
        "four_controls_ge_200_quality_events": sum(profile["quality_rows"] >= 200 for profile in control_profiles) >= 4,
        "four_controls_ge_20_events_each_frozen_year": sum(all(control_year_counts[profile["iau"]][year] >= 20 for year in YEARS) for profile in control_profiles) >= 4,
        "sporadic_ge_2000_quality_events": quality_counts[SPORADIC_NUMBER] >= 2000,
        "state_reconstructable_ge_0_95": state_total / selected_total >= 0.95 if selected_total else False,
        "clone_uncertainties_ge_0_90": uncertainty_total / selected_total >= 0.90 if selected_total else False,
        "controls_span_dynamical_regimes": bool(
            len(inclinations) >= 2
            and max(inclinations) - min(inclinations) >= 20.0
            and (
                (len(semimajor_axes) >= 2 and max(semimajor_axes) - min(semimajor_axes) >= 0.75)
                or (len(tisserand) >= 2 and max(tisserand) - min(tisserand) >= 0.75)
            )
        ),
    }
    verdict = "PROCEED_TO_STATIC_MATCHING_GATE" if all(gates.values()) else "KILL_DYNAMICAL_COHERENCE_DATA_GATE"
    payload = {
        "frozen_years": YEARS,
        "control_months": CONTROL_MONTH,
        "sources": source_files,
        "profiles": profiles,
        "saved_control_events": len(control_events),
        "saved_sporadic_events": len(sporadic_events),
        "sporadic_seen_by_stratum": {f"{year}-{month:02d}": sporadic_seen[(year, month)] for year in YEARS for month in MONTHS},
        "malformed_rows": malformed_rows,
        "gates": gates,
        "verdict": verdict,
    }
    (OUT_DIR / "data_gate.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Predictability-normalized dynamics: labeled GMN data gate",
        "",
        "GhostStream was excluded. Sources are official GMN monthly trajectory summaries.",
        "",
        "| IAU | Quality events | 2019 | 2021 | 2023 | 2025 | State frac. | Sigma frac. |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profile in control_profiles:
        years = profile["year_counts"]
        lines.append(
            f"| {profile['iau']} | {profile['quality_rows']:,} | {years['2019']:,} | {years['2021']:,} | {years['2023']:,} | {years['2025']:,} | {profile['state_fraction']:.3f} | {profile['uncertainty_fraction']:.3f} |"
        )
    lines.extend(["", "## Frozen gates", ""])
    for gate, passed in gates.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend(["", f"Verdict: **{verdict}**"])
    report = "\n".join(lines)
    (OUT_DIR / "DATA_GATE_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
