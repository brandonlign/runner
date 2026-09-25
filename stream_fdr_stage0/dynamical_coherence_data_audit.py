from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import ssl
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

OUT_DIR = Path("stream_fdr_stage0/results/dynamical_coherence_audit")
DATABASE_QUERY_ENDPOINT = "https://explore.globalmeteornetwork.org/gmn_data_store.csv"
SUMMARY_URL = "https://globalmeteornetwork.org/data/traj_summary_data/traj_summary_yearly_2019.txt"
CONTROL_NUMBERS = (4, 6, 7, 10, 13)
SPORADIC_NUMBER = -1
CONTROL_LIMIT = 1000
SPORADIC_LIMIT = 5000
QUERY_BATCH_SIZE = 1000
USER_AGENT = "ghoststream-dynamical-coherence-audit/2.0"
TLS_BYPASS_EVENTS: list[dict[str, str]] = []

REQUIRED_COLUMNS = (
    "unique_trajectory_identifier",
    "beginning_julian_date",
    "beginning_utc_time",
    "shower_iau_no",
    "shower_iau_code",
    "sol_lon_deg",
    "a_au",
    "e",
    "i_deg",
    "peri_deg",
    "node_deg",
    "f_deg",
    "m_deg",
    "q_au",
    "qc_deg",
    "medianfiterr_arcsec",
)
UNCERTAINTY_COLUMNS = (
    "sigma_a_au",
    "sigma_e",
    "sigma_i_deg",
    "sigma_peri_deg",
    "sigma_node_deg",
    "sigma_q_au",
    "sigma_f_deg",
    "sigma_m_deg",
)


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan", "na"}:
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def request_bytes(
    url: str,
    *,
    byte_limit: int | None = None,
    allow_documented_hostname_bypass: bool = False,
) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = urllib.request.urlopen(request, timeout=180)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        is_certificate_failure = isinstance(reason, ssl.SSLCertVerificationError)
        if not (allow_documented_hostname_bypass and is_certificate_failure):
            raise
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        TLS_BYPASS_EVENTS.append(
            {
                "url_host": urllib.parse.urlparse(url).hostname or "",
                "reason": str(reason),
            }
        )
        response = urllib.request.urlopen(request, timeout=180, context=context)

    with response:
        return response.read() if byte_limit is None else response.read(byte_limit)


def select_sql(shower_number: int, limit: int, offset: int) -> str:
    return f"""
SELECT
  meteor.unique_trajectory_identifier,
  julianday(meteor.beginning_utc_time) AS beginning_julian_date,
  meteor.beginning_utc_time,
  shower.iau_no AS shower_iau_no,
  shower.iau_code AS shower_iau_code,
  meteor.sol_lon_deg,
  meteor.a_au,
  meteor_sigma.sigma_8 AS sigma_a_au,
  meteor.e,
  meteor_sigma.sigma_9 AS sigma_e,
  meteor.i_deg,
  meteor_sigma.sigma_10 AS sigma_i_deg,
  meteor.peri_deg,
  meteor_sigma.sigma_11 AS sigma_peri_deg,
  meteor.node_deg,
  meteor_sigma.sigma_12 AS sigma_node_deg,
  meteor.q_au,
  meteor_sigma.sigma_15 AS sigma_q_au,
  meteor.f_deg,
  meteor_sigma.sigma_16 AS sigma_f_deg,
  meteor.m_deg,
  meteor_sigma.sigma_17 AS sigma_m_deg,
  meteor.tisserandj,
  meteor.qc_deg,
  meteor.medianfiterr_arcsec
FROM meteor
LEFT JOIN meteor_sigma
  ON meteor.unique_trajectory_identifier = meteor_sigma.unique_trajectory_identifier
LEFT JOIN shower
  ON meteor.shower_iau_no = shower.iau_no
WHERE meteor.shower_iau_no = {int(shower_number)}
ORDER BY meteor.beginning_utc_time DESC
LIMIT {int(limit)} OFFSET {int(offset)}
""".strip()


def fetch_query_batch(shower_number: int, limit: int, offset: int) -> tuple[list[dict[str, str]], dict[str, str]]:
    sql = select_sql(shower_number, limit, offset)
    parameters = {"sql": sql, "_size": "max"}
    url = DATABASE_QUERY_ENDPOINT + "?" + urllib.parse.urlencode(parameters)
    payload = request_bytes(url, allow_documented_hostname_bypass=True)
    text = payload.decode("utf-8-sig", errors="replace")
    if text.lstrip().lower().startswith("<!doctype html"):
        raise RuntimeError(
            f"GMN explorer returned HTML instead of CSV for shower {shower_number} offset {offset}"
        )
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    return rows, {
        "endpoint": DATABASE_QUERY_ENDPOINT,
        "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "csv_sha256": hashlib.sha256(payload).hexdigest(),
        "offset": str(offset),
        "limit": str(limit),
    }


def fetch_datasette_rows(shower_number: int, requested_limit: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    provenance: list[dict[str, str]] = []
    offset = 0
    while len(rows) < requested_limit:
        batch_limit = min(QUERY_BATCH_SIZE, requested_limit - len(rows))
        batch, batch_provenance = fetch_query_batch(shower_number, batch_limit, offset)
        provenance.append(batch_provenance)
        rows.extend(batch)
        if len(batch) < batch_limit:
            break
        offset += len(batch)
    if not rows:
        raise RuntimeError(f"No rows returned for shower {shower_number}")
    return rows, provenance


def parse_year(value: str | None) -> int | None:
    if not value:
        return None
    text = str(value)
    if len(text) < 4:
        return None
    try:
        year = int(text[:4])
    except ValueError:
        return None
    return year if 1900 <= year <= 2200 else None


def quality_screen(row: dict[str, str]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    a = as_float(row.get("a_au"))
    e = as_float(row.get("e"))
    inc = as_float(row.get("i_deg"))
    peri = as_float(row.get("peri_deg"))
    node = as_float(row.get("node_deg"))
    true_anomaly = as_float(row.get("f_deg"))
    mean_anomaly = as_float(row.get("m_deg"))
    q = as_float(row.get("q_au"))
    qc = as_float(row.get("qc_deg"))
    fit_error = as_float(row.get("medianfiterr_arcsec"))
    epoch = as_float(row.get("beginning_julian_date"))

    if a is None or not (0.0 < a < 100.0):
        failures.append("a")
    if e is None or not (0.0 <= e < 1.2):
        failures.append("e")
    if inc is None or not (0.0 <= inc <= 180.0):
        failures.append("i")
    if peri is None or not (0.0 <= peri < 360.0):
        failures.append("peri")
    if node is None or not (0.0 <= node < 360.0):
        failures.append("node")
    if true_anomaly is None and mean_anomaly is None:
        failures.append("anomaly")
    if q is None or not (0.0 < q < 1.3):
        failures.append("q")
    if epoch is None:
        failures.append("epoch")
    if qc is not None and qc < 10.0:
        failures.append("qc")
    if fit_error is not None and fit_error > 300.0:
        failures.append("fit_error")
    return not failures, failures


def uncertainty_reconstructable(row: dict[str, str]) -> bool:
    fixed = ("sigma_a_au", "sigma_e", "sigma_i_deg", "sigma_peri_deg", "sigma_node_deg")
    if not all(
        (value := as_float(row.get(column))) is not None and value >= 0.0
        for column in fixed
    ):
        return False
    sigma_f = as_float(row.get("sigma_f_deg"))
    sigma_m = as_float(row.get("sigma_m_deg"))
    return bool(
        (sigma_f is not None and sigma_f >= 0.0)
        or (sigma_m is not None and sigma_m >= 0.0)
    )


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


def profile_rows(
    shower_number: int,
    rows: list[dict[str, str]],
    query_provenance: list[dict[str, str]],
) -> dict[str, Any]:
    header = list(rows[0].keys())
    missing_required = [column for column in REQUIRED_COLUMNS if column not in header]
    missing_uncertainty = [column for column in UNCERTAINTY_COLUMNS if column not in header]
    screened: list[dict[str, str]] = []
    failure_counts: Counter[str] = Counter()
    for row in rows:
        passes, failures = quality_screen(row)
        if passes:
            screened.append(row)
        else:
            failure_counts.update(failures)

    years = Counter(
        year
        for row in screened
        if (year := parse_year(row.get("beginning_utc_time"))) is not None
    )
    iau_codes = Counter(
        (row.get("shower_iau_code") or "").strip()
        for row in screened
    )

    numeric_columns = {
        "a_au": [],
        "e": [],
        "i_deg": [],
        "q_au": [],
        "qc_deg": [],
        "medianfiterr_arcsec": [],
        "tisserandj": [],
    }
    for row in screened:
        for column in numeric_columns:
            value = as_float(row.get(column))
            if value is not None:
                numeric_columns[column].append(value)

    reconstructable = sum(
        1
        for row in rows
        if all(
            as_float(row.get(column)) is not None
            for column in (
                "beginning_julian_date",
                "a_au",
                "e",
                "i_deg",
                "peri_deg",
                "node_deg",
            )
        )
        and (
            as_float(row.get("f_deg")) is not None
            or as_float(row.get("m_deg")) is not None
        )
    )
    uncertainty_rows = sum(uncertainty_reconstructable(row) for row in screened)

    return {
        "shower_number": shower_number,
        "query_provenance": query_provenance,
        "retrieved_rows": len(rows),
        "header": header,
        "missing_required_columns": missing_required,
        "missing_uncertainty_columns": missing_uncertainty,
        "quality_screened_rows": len(screened),
        "quality_screened_fraction": len(screened) / len(rows),
        "failure_counts": dict(failure_counts),
        "year_counts": {str(year): count for year, count in sorted(years.items())},
        "year_count": len(years),
        "iau_code_counts": dict(iau_codes),
        "state_reconstructable_rows": reconstructable,
        "state_reconstructable_fraction": reconstructable / len(rows),
        "clone_uncertainty_rows": uncertainty_rows,
        "clone_uncertainty_fraction_of_screened": (
            uncertainty_rows / len(screened) if screened else 0.0
        ),
        "numeric_quantiles": {
            column: quantiles(values) for column, values in numeric_columns.items()
        },
    }


def inspect_summary_header() -> dict[str, Any]:
    payload = request_bytes(SUMMARY_URL, byte_limit=300_000)
    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines()
    preview = lines[:80]
    lower = text.lower()
    uncertainty_markers = {
        "sigma": "sigma" in lower,
        "plus_minus": "+/-" in text or "±" in text,
        "uncertainty": "uncert" in lower,
    }
    return {
        "source_url": SUMMARY_URL,
        "bytes_inspected": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "line_count_inspected": len(lines),
        "uncertainty_markers": uncertainty_markers,
        "preview": preview,
    }


def regime_spread(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    controls = [p for p in profiles if p["shower_number"] in CONTROL_NUMBERS]
    medians: dict[int, dict[str, float]] = {}
    for profile in controls:
        values: dict[str, float] = {}
        for column in ("a_au", "e", "i_deg", "q_au", "tisserandj"):
            median = profile["numeric_quantiles"][column]["p50"]
            if median is not None:
                values[column] = float(median)
        medians[int(profile["shower_number"])] = values

    inclinations = [values["i_deg"] for values in medians.values() if "i_deg" in values]
    semimajor_axes = [values["a_au"] for values in medians.values() if "a_au" in values]
    tisserand = [values["tisserandj"] for values in medians.values() if "tisserandj" in values]
    return {
        "control_medians": medians,
        "inclination_range_deg": max(inclinations) - min(inclinations) if len(inclinations) >= 2 else None,
        "semimajor_axis_range_au": max(semimajor_axes) - min(semimajor_axes) if len(semimajor_axes) >= 2 else None,
        "tisserand_range": max(tisserand) - min(tisserand) if len(tisserand) >= 2 else None,
    }


def make_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Predictability-normalized dynamical coherence: data audit",
        "",
        "This audit ran only in `brandonlign/runner`. GhostStream was excluded.",
        "",
        "## Event-level controls",
        "",
        "| IAU no. | Codes observed | Retrieved | Quality-screened | Years | State | Clone uncertainties |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for profile in payload["profiles"]:
        codes = ", ".join(
            code or "(blank)" for code in profile["iau_code_counts"].keys()
        )
        lines.append(
            f"| {profile['shower_number']} | {codes} | {profile['retrieved_rows']:,} "
            f"| {profile['quality_screened_rows']:,} | {profile['year_count']} "
            f"| {profile['state_reconstructable_fraction']:.3f} "
            f"| {profile['clone_uncertainty_fraction_of_screened']:.3f} |"
        )

    lines.extend([
        "",
        "## Data-transport note",
        "",
        f"- explorer TLS hostname-bypass events: {len(payload['tls_hostname_bypass_events'])}",
        "- Each returned batch is preserved by SQL and CSV SHA-256 in `audit.json`.",
        "- This bypass is acceptable only for feasibility; a scientific benchmark must cross-check selected event rows against the official trajectory summaries.",
        "",
        "## Uncertainty schema",
        "",
        f"- official trajectory-summary bytes inspected: {payload['summary_header']['bytes_inspected']:,}",
        f"- uncertainty markers: `{json.dumps(payload['summary_header']['uncertainty_markers'], sort_keys=True)}`",
        "",
        "## Regime spread",
        "",
        f"- median-inclination range: {payload['regime_spread']['inclination_range_deg']}",
        f"- median-semimajor-axis range: {payload['regime_spread']['semimajor_axis_range_au']}",
        f"- median-Tisserand range: {payload['regime_spread']['tisserand_range']}",
        "",
        "## Frozen feasibility gates",
        "",
    ])
    for gate, passed in payload["gates"].items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{gate}`")
    lines.extend(["", f"Verdict: **{payload['verdict']}**"])
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profiles: list[dict[str, Any]] = []
    for shower_number in (*CONTROL_NUMBERS, SPORADIC_NUMBER):
        limit = SPORADIC_LIMIT if shower_number == SPORADIC_NUMBER else CONTROL_LIMIT
        rows, provenance = fetch_datasette_rows(shower_number, limit)
        profiles.append(profile_rows(shower_number, rows, provenance))

    summary_header = inspect_summary_header()
    spread = regime_spread(profiles)
    controls = [p for p in profiles if p["shower_number"] in CONTROL_NUMBERS]
    sporadic = next(p for p in profiles if p["shower_number"] == SPORADIC_NUMBER)
    controls_ge_200 = sum(p["quality_screened_rows"] >= 200 for p in controls)
    all_selected = sum(p["retrieved_rows"] for p in profiles)
    reconstructable = sum(p["state_reconstructable_rows"] for p in profiles)
    all_screened = sum(p["quality_screened_rows"] for p in profiles)
    uncertainty_rows = sum(p["clone_uncertainty_rows"] for p in profiles)
    uncertainty_schema_found = all(
        not profile["missing_uncertainty_columns"] for profile in profiles
    )
    regime_diverse = bool(
        (spread["inclination_range_deg"] or 0.0) >= 20.0
        and (
            (spread["semimajor_axis_range_au"] or 0.0) >= 0.75
            or (spread["tisserand_range"] or 0.0) >= 0.75
        )
    )

    gates = {
        "four_controls_ge_200_quality_events": controls_ge_200 >= 4,
        "sporadic_ge_2000_quality_events": sporadic["quality_screened_rows"] >= 2000,
        "state_reconstructable_ge_0_95": reconstructable / all_selected >= 0.95,
        "uncertainty_schema_detected": uncertainty_schema_found,
        "clone_uncertainty_reconstructable_ge_0_90": (
            uncertainty_rows / all_screened >= 0.90 if all_screened else False
        ),
        "controls_span_multiple_dynamical_regimes": regime_diverse,
    }
    fatal = (
        gates["four_controls_ge_200_quality_events"]
        and gates["sporadic_ge_2000_quality_events"]
        and gates["state_reconstructable_ge_0_95"]
    )
    uncertainty_ready = (
        gates["uncertainty_schema_detected"]
        and gates["clone_uncertainty_reconstructable_ge_0_90"]
    )
    verdict = (
        "PROCEED_TO_PREDICTABILITY_NORMALIZED_DYNAMICAL_SURROGATE"
        if fatal and uncertainty_ready
        else "PROCEED_NOMINAL_ONLY_NO_PREDICTABILITY_CLAIM"
        if fatal
        else "KILL_DYNAMICAL_COHERENCE_DATA_FEASIBILITY"
    )

    payload = {
        "profiles": profiles,
        "summary_header": summary_header,
        "tls_hostname_bypass_events": TLS_BYPASS_EVENTS,
        "regime_spread": spread,
        "gates": gates,
        "verdict": verdict,
    }
    (OUT_DIR / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = make_report(payload)
    (OUT_DIR / "AUDIT_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
