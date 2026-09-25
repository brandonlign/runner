from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

OUT_DIR = Path("dynamics_audit/results")
DATA_DIR = Path("dynamics_audit/data")
DATA_PATH = DATA_DIR / "GMN_shober_2026_subset.csv"
DATA_URL = "https://zenodo.org/records/18664293/files/GMN_shober_2026_subset.csv?download=1"
EXPECTED_MD5 = "a1890dcb0ca11baa0e49c21c2133dc55"
CONTROL_NUMBERS = (4, 6, 7, 10, 13)
SPORADIC_NUMBER = -1
USER_AGENT = "ghoststream-dynamical-data-audit/1.0"

STATE_COLUMNS = (
    "Beginning_Julian_date",
    "a_AU",
    "e",
    "i_deg",
    "peri_deg",
    "node_deg",
)
SIGMA_COLUMNS = (
    "a_sigma",
    "e_sigma",
    "i_sigma",
    "peri_sigma",
    "node_sigma",
)


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    if number is None or abs(number - round(number)) > 1e-8:
        return None
    return int(round(number))


def parse_year(value: str | None) -> int | None:
    text = (value or "").strip()
    if len(text) < 4:
        return None
    try:
        year = int(text[:4])
    except ValueError:
        return None
    return year if 1900 <= year <= 2200 else None


def download() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        return
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=240) as response, DATA_PATH.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"p05": None, "p50": None, "p95": None}
    ordered = sorted(values)

    def one(probability: float) -> float:
        position = probability * (len(ordered) - 1)
        lo = int(math.floor(position))
        hi = int(math.ceil(position))
        if lo == hi:
            return ordered[lo]
        fraction = position - lo
        return ordered[lo] * (1.0 - fraction) + ordered[hi] * fraction

    return {"p05": one(0.05), "p50": one(0.50), "p95": one(0.95)}


def valid_state(row: dict[str, str]) -> bool:
    values = {column: as_float(row.get(column)) for column in STATE_COLUMNS}
    anomaly = as_float(row.get("f_deg"))
    if anomaly is None:
        anomaly = as_float(row.get("M_deg"))
    if any(values[column] is None for column in STATE_COLUMNS) or anomaly is None:
        return False
    assert all(value is not None for value in values.values())
    return bool(
        values["Beginning_Julian_date"] > 2_000_000
        and 0.0 < values["a_AU"] < 100.0
        and 0.0 <= values["e"] < 1.2
        and 0.0 <= values["i_deg"] <= 180.0
        and 0.0 <= values["peri_deg"] < 360.0
        and 0.0 <= values["node_deg"] < 360.0
    )


def valid_uncertainties(row: dict[str, str]) -> bool:
    fixed = [as_float(row.get(column)) for column in SIGMA_COLUMNS]
    anomaly_sigma = as_float(row.get("f_sigma"))
    if anomaly_sigma is None:
        anomaly_sigma = as_float(row.get("M_sigma"))
    return bool(
        all(value is not None and value >= 0.0 for value in fixed)
        and anomaly_sigma is not None
        and anomaly_sigma >= 0.0
    )


def passes_quality(row: dict[str, str]) -> bool:
    if not valid_state(row):
        return False
    q = as_float(row.get("q_AU"))
    qc = as_float(row.get("Qc_deg"))
    fit_error = as_float(row.get("MedianFitErr_arcsec"))
    return bool(
        q is not None
        and 0.0 < q < 1.3
        and (qc is None or qc >= 10.0)
        and (fit_error is None or fit_error <= 300.0)
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    download()
    md5 = file_hash(DATA_PATH, "md5")
    sha256 = file_hash(DATA_PATH, "sha256")
    if md5 != EXPECTED_MD5:
        raise RuntimeError(f"GMN input MD5 mismatch: expected {EXPECTED_MD5}, got {md5}")

    selected = set(CONTROL_NUMBERS) | {SPORADIC_NUMBER}
    counts: Counter[int] = Counter()
    quality_counts: Counter[int] = Counter()
    state_counts: Counter[int] = Counter()
    uncertainty_counts: Counter[int] = Counter()
    years: dict[int, Counter[int]] = defaultdict(Counter)
    codes: dict[int, Counter[str]] = defaultdict(Counter)
    numeric: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    total_rows = 0
    header: list[str] = []

    with DATA_PATH.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        for row in reader:
            total_rows += 1
            shower = as_int(row.get("IAU"))
            if shower not in selected:
                continue
            assert shower is not None
            counts[shower] += 1
            state_ok = valid_state(row)
            uncertainty_ok = valid_uncertainties(row)
            quality_ok = passes_quality(row)
            if state_ok:
                state_counts[shower] += 1
            if uncertainty_ok:
                uncertainty_counts[shower] += 1
            if not quality_ok:
                continue
            quality_counts[shower] += 1
            year = parse_year(row.get("Beginning_UTC_Time"))
            if year is not None:
                years[shower][year] += 1
            codes[shower][(row.get("IAU.1") or "").strip()] += 1
            for column in ("a_AU", "e", "i_deg", "q_AU", "TisserandJ"):
                value = as_float(row.get(column))
                if value is not None:
                    numeric[shower][column].append(value)

    profiles: list[dict[str, Any]] = []
    for shower in (*CONTROL_NUMBERS, SPORADIC_NUMBER):
        retrieved = counts[shower]
        profile = {
            "shower_number": shower,
            "codes": dict(codes[shower]),
            "retrieved_rows": retrieved,
            "quality_rows": quality_counts[shower],
            "quality_fraction": quality_counts[shower] / retrieved if retrieved else 0.0,
            "state_fraction": state_counts[shower] / retrieved if retrieved else 0.0,
            "uncertainty_fraction": uncertainty_counts[shower] / retrieved if retrieved else 0.0,
            "year_counts": {str(year): count for year, count in sorted(years[shower].items())},
            "year_count": len(years[shower]),
            "quantiles": {
                column: quantiles(values)
                for column, values in numeric[shower].items()
            },
        }
        profiles.append(profile)

    controls = [profile for profile in profiles if profile["shower_number"] in CONTROL_NUMBERS]
    sporadic = next(profile for profile in profiles if profile["shower_number"] == SPORADIC_NUMBER)
    controls_ge_200 = sum(profile["quality_rows"] >= 200 for profile in controls)
    controls_four_years = sum(profile["year_count"] >= 4 for profile in controls)
    selected_rows = sum(profile["retrieved_rows"] for profile in profiles)
    selected_state = sum(state_counts[profile["shower_number"]] for profile in profiles)
    selected_uncertainty = sum(uncertainty_counts[profile["shower_number"]] for profile in profiles)

    medians = {
        profile["shower_number"]: {
            column: profile["quantiles"].get(column, {}).get("p50")
            for column in ("a_AU", "i_deg", "TisserandJ")
        }
        for profile in controls
    }
    inclinations = [value["i_deg"] for value in medians.values() if value["i_deg"] is not None]
    semimajor_axes = [value["a_AU"] for value in medians.values() if value["a_AU"] is not None]
    tisserand = [value["TisserandJ"] for value in medians.values() if value["TisserandJ"] is not None]
    regime_spread = {
        "control_medians": medians,
        "inclination_range_deg": max(inclinations) - min(inclinations) if len(inclinations) >= 2 else None,
        "semimajor_axis_range_au": max(semimajor_axes) - min(semimajor_axes) if len(semimajor_axes) >= 2 else None,
        "tisserand_range": max(tisserand) - min(tisserand) if len(tisserand) >= 2 else None,
    }

    gates = {
        "four_controls_ge_200_quality_events": controls_ge_200 >= 4,
        "four_controls_span_ge_4_years": controls_four_years >= 4,
        "sporadic_ge_2000_quality_events": sporadic["quality_rows"] >= 2000,
        "state_reconstructable_ge_0_95": selected_state / selected_rows >= 0.95 if selected_rows else False,
        "clone_uncertainties_ge_0_90": selected_uncertainty / selected_rows >= 0.90 if selected_rows else False,
        "controls_span_dynamical_regimes": bool(
            (regime_spread["inclination_range_deg"] or 0.0) >= 20.0
            and (
                (regime_spread["semimajor_axis_range_au"] or 0.0) >= 0.75
                or (regime_spread["tisserand_range"] or 0.0) >= 0.75
            )
        ),
    }
    verdict = (
        "PROCEED_TO_PREDICTABILITY_NORMALIZED_DYNAMICAL_SURROGATE"
        if all(gates.values())
        else "KILL_DYNAMICAL_COHERENCE_DATA_FEASIBILITY"
    )

    payload = {
        "source": {
            "url": DATA_URL,
            "path": str(DATA_PATH),
            "bytes": DATA_PATH.stat().st_size,
            "md5": md5,
            "sha256": sha256,
            "total_rows": total_rows,
            "header": header,
        },
        "profiles": profiles,
        "regime_spread": regime_spread,
        "gates": gates,
        "verdict": verdict,
    }
    (OUT_DIR / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# GMN dynamical-coherence data audit",
        "",
        "This audit used the checksum-verified Zenodo GMN subset. GhostStream was excluded.",
        "",
        "| IAU no. | Codes | Retrieved | Quality | Years | State frac. | Sigma frac. |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for profile in profiles:
        code_text = ", ".join(code or "(blank)" for code in profile["codes"])
        lines.append(
            f"| {profile['shower_number']} | {code_text} | {profile['retrieved_rows']:,} "
            f"| {profile['quality_rows']:,} | {profile['year_count']} "
            f"| {profile['state_fraction']:.3f} | {profile['uncertainty_fraction']:.3f} |"
        )
    lines.extend(["", "## Frozen gates", ""])
    for gate, passed in gates.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend([
        "",
        f"Verdict: **{verdict}**",
        "",
        f"Input MD5: `{md5}`",
        f"Input SHA-256: `{sha256}`",
    ])
    report = "\n".join(lines)
    (OUT_DIR / "AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
