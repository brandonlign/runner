from __future__ import annotations

import csv
import gzip
import hashlib
import html
import json
import math
import random
import re
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("real_shower_meta_stage0")
OUT_DIR = ROOT / "results" / "data_audit"
YEARS = (2019, 2021, 2023, 2025)
MONTHS = tuple(range(1, 13))
MONTHLY_URL = "https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt"
MDC_URL = "https://ceresiaumdc.ta3.sk/downloads/lists_shw_data/streamfulldata.json"
USER_AGENT = "ghoststream-real-shower-meta-audit/1.0"
LABELED_RESERVOIR_PER_SHOWER_YEAR = 500
SPORADIC_RESERVOIR_PER_YEAR_MONTH = 5000

IDX = {
    "id": 0,
    "jd": 1,
    "utc": 2,
    "iau": 3,
    "code": 4,
    "sol": 5,
    "ra": 7,
    "ra_sigma": 8,
    "dec": 9,
    "dec_sigma": 10,
    "vg": 15,
    "vg_sigma": 16,
    "a": 23,
    "e": 25,
    "i": 27,
    "peri": 29,
    "node": 31,
    "q": 37,
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
    if shower == 0 or shower < -1:
        return None

    sol = as_float(value(row, "sol"))
    ra = as_float(value(row, "ra"))
    dec = as_float(value(row, "dec"))
    vg = as_float(value(row, "vg"))
    ra_sigma = as_float(value(row, "ra_sigma"))
    dec_sigma = as_float(value(row, "dec_sigma"))
    vg_sigma = as_float(value(row, "vg_sigma"))
    qc = as_float(value(row, "Qc"))
    fiterr = as_float(value(row, "fiterr"))
    num_stat = as_int(value(row, "num_stat"))

    complete = bool(
        sol is not None
        and 0.0 <= sol < 360.0
        and ra is not None
        and 0.0 <= ra < 360.0
        and dec is not None
        and -90.0 <= dec <= 90.0
        and vg is not None
        and 5.0 <= vg <= 80.0
        and ra_sigma is not None
        and ra_sigma >= 0.0
        and dec_sigma is not None
        and dec_sigma >= 0.0
        and vg_sigma is not None
        and vg_sigma >= 0.0
    )
    quality = bool(
        complete
        and (qc is None or qc >= 10.0)
        and (fiterr is None or fiterr <= 300.0)
        and (num_stat is None or num_stat >= 2)
    )
    if not quality:
        return None

    return {
        "id": value(row, "id"),
        "year": year,
        "month": month,
        "iau": shower,
        "code": value(row, "code") or "",
        "sol": sol,
        "ra": ra,
        "dec": dec,
        "vg": vg,
        "ra_sigma": ra_sigma,
        "dec_sigma": dec_sigma,
        "vg_sigma": vg_sigma,
        "a": as_float(value(row, "a")),
        "e": as_float(value(row, "e")),
        "i": as_float(value(row, "i")),
        "peri": as_float(value(row, "peri")),
        "node": as_float(value(row, "node")),
        "q": as_float(value(row, "q")),
        "Qc": qc,
        "fiterr": fiterr,
        "num_stat": num_stat,
    }


def request_to_file(url: str, path: Path) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(request, timeout=300) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
            output.write(chunk)
        return {
            "url": url,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def request_json(url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        raw = response.read()
        metadata = {
            "url": url,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
        }
    return json.loads(raw), metadata


def normalize_parent(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    text = " ".join(text.replace("\u00a0", " ").split()).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:120]


def mdc_complex_map(payload: dict[str, Any]) -> tuple[dict[int, str], dict[int, dict[str, Any]]]:
    mapping: dict[int, str] = {}
    metadata: dict[int, dict[str, Any]] = {}
    for shower in payload.get("data", []):
        try:
            iau = int(str(shower.get("IAUNo", "")).strip())
        except ValueError:
            continue
        group_values: list[str] = []
        parents: list[str] = []
        for solution in shower.get("solution", []) or []:
            group = str(solution.get("Group") or "").strip()
            if group and group not in {"0", "00", "000", "0000", "00000", "-"}:
                group_values.append(group)
            parent = str(solution.get("Parent body") or solution.get("Origin") or "").strip()
            if normalize_parent(parent):
                parents.append(parent)
        if group_values:
            key = f"MDC_GROUP:{Counter(group_values).most_common(1)[0][0]}"
        elif parents:
            normalized = normalize_parent(Counter(parents).most_common(1)[0][0])
            key = f"PARENT:{normalized}"
        else:
            key = f"SHOWER:{iau}"
        mapping[iau] = key
        metadata[iau] = {
            "complex_key": key,
            "code": shower.get("Code"),
            "name": shower.get("Name") or shower.get("ProvName"),
            "status": shower.get("s"),
            "group_values": group_values,
            "parent_values": parents,
        }
    return mapping, metadata


def reservoir_add(
    reservoirs: dict[tuple[Any, ...], list[dict[str, Any]]],
    seen: Counter[tuple[Any, ...]],
    key: tuple[Any, ...],
    event: dict[str, Any],
    limit: int,
    rngs: dict[tuple[Any, ...], random.Random],
) -> None:
    seen[key] += 1
    bucket = reservoirs[key]
    if len(bucket) < limit:
        bucket.append(event)
        return
    if key not in rngs:
        rngs[key] = random.Random(int.from_bytes(hashlib.sha256(repr(key).encode()).digest()[:8], "big"))
    index = rngs[key].randrange(seen[key])
    if index < limit:
        bucket[index] = event


def circular_width_90(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(value % 360.0 for value in values)
    doubled = ordered + [value + 360.0 for value in ordered]
    count = max(1, int(math.ceil(0.90 * len(ordered))))
    return min(doubled[index + count - 1] - doubled[index] for index in range(len(ordered)))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mdc, mdc_source = request_json(MDC_URL)
    complex_map, mdc_metadata = mdc_complex_map(mdc)

    counts: Counter[int] = Counter()
    year_counts: dict[int, Counter[int]] = defaultdict(Counter)
    code_counts: dict[int, Counter[str]] = defaultdict(Counter)
    labeled_reservoirs: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    sporadic_reservoirs: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    labeled_seen: Counter[tuple[Any, ...]] = Counter()
    sporadic_seen: Counter[tuple[Any, ...]] = Counter()
    rngs: dict[tuple[Any, ...], random.Random] = {}
    sources: list[dict[str, Any]] = []
    malformed = 0
    total_rows = 0
    quality_rows = 0

    with tempfile.TemporaryDirectory(prefix="gmn_meta_audit_") as temporary:
        temporary_root = Path(temporary)
        for year in YEARS:
            for month in MONTHS:
                url = MONTHLY_URL.format(year=year, month=month)
                path = temporary_root / f"{year}{month:02d}.txt"
                source = request_to_file(url, path)
                source.update({"year": year, "month": month})
                sources.append(source)
                with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                    reader = csv.reader(handle, delimiter=";")
                    for row in reader:
                        if not row or row[0].lstrip().startswith("#"):
                            continue
                        total_rows += 1
                        if len(row) <= IDX["num_stat"]:
                            malformed += 1
                            continue
                        event = parse_event(row, year, month)
                        if event is None:
                            continue
                        quality_rows += 1
                        iau = int(event["iau"])
                        counts[iau] += 1
                        if iau > 0:
                            year_counts[iau][year] += 1
                            code_counts[iau][str(event["code"])] += 1
                            reservoir_add(
                                labeled_reservoirs,
                                labeled_seen,
                                (iau, year),
                                event,
                                LABELED_RESERVOIR_PER_SHOWER_YEAR,
                                rngs,
                            )
                        elif iau == -1:
                            reservoir_add(
                                sporadic_reservoirs,
                                sporadic_seen,
                                (year, month),
                                event,
                                SPORADIC_RESERVOIR_PER_YEAR_MONTH,
                                rngs,
                            )
                path.unlink(missing_ok=True)

    profiles: list[dict[str, Any]] = []
    for iau in sorted(key for key in counts if key > 0):
        years = year_counts[iau]
        sampled = [event for year in YEARS for event in labeled_reservoirs.get((iau, year), [])]
        width = circular_width_90([float(event["sol"]) for event in sampled])
        profile = {
            "iau": iau,
            "codes": dict(code_counts[iau]),
            "quality_events": counts[iau],
            "year_counts": {str(year): years[year] for year in YEARS},
            "represented_years": sum(years[year] > 0 for year in YEARS),
            "years_ge_20": sum(years[year] >= 20 for year in YEARS),
            "solar_longitude_90pct_width_deg": width,
            "complex_key": complex_map.get(iau, f"SHOWER:{iau}"),
            "mdc": mdc_metadata.get(iau),
        }
        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] >= 3
            and profile["years_ge_20"] >= 3
        )
        profile["strong"] = bool(profile["quality_events"] >= 1000 and profile["represented_years"] == 4)
        profiles.append(profile)

    eligible = [profile for profile in profiles if profile["eligible"]]
    strong = [profile for profile in profiles if profile["strong"]]
    complex_members: dict[str, list[int]] = defaultdict(list)
    for profile in eligible:
        complex_members[str(profile["complex_key"])].append(int(profile["iau"]))
    multi_shower_complexes = {key: members for key, members in complex_members.items() if len(members) >= 2}
    high_leakage = sum(
        profile["solar_longitude_90pct_width_deg"] is not None
        and profile["solar_longitude_90pct_width_deg"] <= 20.0
        for profile in eligible
    )
    total_sporadic_quality = counts[-1]

    selected_labeled: list[dict[str, Any]] = []
    eligible_ids = {int(profile["iau"]) for profile in eligible}
    for (iau, _year), events in sorted(labeled_reservoirs.items()):
        if int(iau) not in eligible_ids:
            continue
        complex_key = complex_map.get(int(iau), f"SHOWER:{iau}")
        for event in events:
            event = dict(event)
            event["complex_key"] = complex_key
            selected_labeled.append(event)
    selected_sporadic = [event for key in sorted(sporadic_reservoirs) for event in sporadic_reservoirs[key]]
    selected = selected_labeled + selected_sporadic
    complete_selected = sum(
        all(event.get(field) is not None for field in ("sol", "ra", "dec", "vg", "ra_sigma", "dec_sigma", "vg_sigma"))
        for event in selected
    )
    complete_fraction = complete_selected / len(selected) if selected else 0.0

    with gzip.open(OUT_DIR / "selected_events.jsonl.gz", "wt", encoding="utf-8") as output:
        for event in selected:
            output.write(json.dumps(event, sort_keys=True) + "\n")

    gates = {
        "eligible_showers_at_least_30": len(eligible) >= 30,
        "strong_showers_at_least_12": len(strong) >= 12,
        "eligible_complex_units_at_least_20": len(complex_members) >= 20,
        "multi_shower_complex_units_at_least_6": len(multi_shower_complexes) >= 6,
        "quality_sporadics_at_least_200000": total_sporadic_quality >= 200_000,
        "selected_complete_fraction_at_least_0_95": complete_fraction >= 0.95,
    }
    verdict = (
        "PROCEED_TO_COMPLEX_HELDOUT_EPISODIC_PILOT"
        if all(gates.values())
        else "KILL_REAL_SHOWER_META_DATA_FEASIBILITY"
    )
    payload = {
        "configuration": {
            "years": YEARS,
            "months": MONTHS,
            "labeled_reservoir_per_shower_year": LABELED_RESERVOIR_PER_SHOWER_YEAR,
            "sporadic_reservoir_per_year_month": SPORADIC_RESERVOIR_PER_YEAR_MONTH,
        },
        "sources": sources,
        "mdc_source": mdc_source,
        "mdc_version": mdc.get("version"),
        "total_rows": total_rows,
        "quality_rows": quality_rows,
        "malformed_rows": malformed,
        "total_quality_sporadics": total_sporadic_quality,
        "profiles": profiles,
        "eligible_count": len(eligible),
        "strong_count": len(strong),
        "eligible_complex_units": len(complex_members),
        "multi_shower_complex_units": multi_shower_complexes,
        "eligible_high_solar_leakage_count": high_leakage,
        "eligible_high_solar_leakage_fraction": high_leakage / len(eligible) if eligible else 0.0,
        "saved_labeled_events": len(selected_labeled),
        "saved_sporadic_events": len(selected_sporadic),
        "selected_complete_fraction": complete_fraction,
        "gates": gates,
        "verdict": verdict,
    }
    (OUT_DIR / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Real-shower meta-learning data audit",
        "",
        "GhostStream was excluded. Data came from 48 official GMN monthly trajectory summaries and the IAU MDC shower file.",
        "",
        f"- eligible showers: **{len(eligible)}**",
        f"- strong showers: **{len(strong)}**",
        f"- eligible complex units: **{len(complex_members)}**",
        f"- multi-shower complex units: **{len(multi_shower_complexes)}**",
        f"- quality sporadics: **{total_sporadic_quality:,}**",
        f"- saved labeled events: **{len(selected_labeled):,}**",
        f"- saved sporadic events: **{len(selected_sporadic):,}**",
        f"- eligible showers with <=20 degree 90% solar-longitude width: **{high_leakage}/{len(eligible)}**",
        "",
        "## Frozen gates",
        "",
    ]
    for gate, passed in gates.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend(["", f"Verdict: **{verdict}**"])
    report = "\n".join(lines)
    (OUT_DIR / "AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
