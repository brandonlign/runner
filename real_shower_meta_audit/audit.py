from __future__ import annotations

import hashlib
import json
import math
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

BASE = "https://explore.globalmeteornetwork.org/gmn_rest_api"
OUT = Path("real_shower_meta_audit/results")


def query(sql: str) -> tuple[Any, dict[str, str]]:
    params = urllib.parse.urlencode(
        {"sql": sql, "data_shape": "objects", "data_format": "json"}
    )
    url = f"{BASE}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "GhostStream-method-audit/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type.lower() and not raw.lstrip().startswith((b"[", b"{")):
        raise RuntimeError(f"Expected JSON from {url}, got {content_type}: {raw[:200]!r}")
    payload = json.loads(raw.decode("utf-8"))
    # The endpoint may return either a direct list or a wrapper containing rows.
    if isinstance(payload, dict):
        for key in ("rows", "data", "results"):
            if key in payload and isinstance(payload[key], list):
                payload = payload[key]
                break
    return payload, {
        "url": url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": str(len(raw)),
    }


def rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise RuntimeError(f"Unexpected API payload type: {type(payload).__name__}")
    if not all(isinstance(item, dict) for item in payload):
        raise RuntimeError("Expected a list of JSON objects")
    return payload


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    aggregate_sql = """
    SELECT
      m.shower_iau_no AS iau_no,
      s.iau_code AS iau_code,
      s.iau_name AS iau_name,
      COUNT(*) AS meteor_count,
      COUNT(DISTINCT substr(m.beginning_utc_time, 1, 4)) AS year_count,
      MIN(substr(m.beginning_utc_time, 1, 4)) AS first_year,
      MAX(substr(m.beginning_utc_time, 1, 4)) AS last_year,
      MIN(m.sol_lon_deg) AS min_sol_lon_deg,
      MAX(m.sol_lon_deg) AS max_sol_lon_deg,
      AVG(m.vgeo_km_s) AS mean_vgeo_km_s
    FROM meteor AS m
    JOIN shower AS s ON s.iau_no = m.shower_iau_no
    WHERE m.shower_iau_no IS NOT NULL
      AND m.shower_iau_no > 0
      AND m.sol_lon_deg IS NOT NULL
      AND m.rageo_deg IS NOT NULL
      AND m.decgeo_deg IS NOT NULL
      AND m.vgeo_km_s IS NOT NULL
    GROUP BY m.shower_iau_no, s.iau_code, s.iau_name
    ORDER BY meteor_count DESC
    """
    aggregate_payload, aggregate_provenance = query(aggregate_sql)
    shower_rows = rows(aggregate_payload)

    eligible = [
        row for row in shower_rows
        if int(row.get("meteor_count") or 0) >= 200
        and int(row.get("year_count") or 0) >= 3
        and finite(row.get("mean_vgeo_km_s"))
    ]
    strong = [
        row for row in shower_rows
        if int(row.get("meteor_count") or 0) >= 1000
        and int(row.get("year_count") or 0) >= 5
    ]

    # Pull capped examples for the largest eligible showers. The audit does not train a model.
    sample_summary: list[dict[str, Any]] = []
    sample_provenance: list[dict[str, str]] = []
    for shower in eligible[:20]:
        iau_no = int(shower["iau_no"])
        sample_sql = f"""
        SELECT
          unique_trajectory_identifier,
          beginning_utc_time,
          shower_iau_no,
          sol_lon_deg,
          rageo_deg,
          decgeo_deg,
          vgeo_km_s,
          a_au,
          e,
          i_deg,
          peri_deg,
          node_deg,
          q_au,
          medianfiterr_arcsec
        FROM meteor
        WHERE shower_iau_no = {iau_no}
          AND sol_lon_deg IS NOT NULL
          AND rageo_deg IS NOT NULL
          AND decgeo_deg IS NOT NULL
          AND vgeo_km_s IS NOT NULL
        ORDER BY beginning_utc_time
        LIMIT 1000
        """
        payload, provenance = query(sample_sql)
        sampled = rows(payload)
        years = Counter(str(row.get("beginning_utc_time", ""))[:4] for row in sampled)
        sample_summary.append(
            {
                "iau_no": iau_no,
                "iau_code": shower.get("iau_code"),
                "returned_rows": len(sampled),
                "sample_year_count": len([year for year in years if year]),
                "sample_year_counts": dict(sorted(years.items())),
                "complete_geocentric_rows": sum(
                    finite(row.get(field))
                    for row in sampled
                    for field in ()
                ),
                "all_required_finite": sum(
                    all(finite(row.get(field)) for field in ("sol_lon_deg", "rageo_deg", "decgeo_deg", "vgeo_km_s"))
                    for row in sampled
                ),
            }
        )
        sample_provenance.append(provenance)

    # Quantify how dangerous solar-longitude leakage is before any model is built.
    # For each eligible shower, estimate the narrowest circular interval containing 90% of its capped sample.
    leakage: list[dict[str, Any]] = []
    for shower in eligible[:20]:
        iau_no = int(shower["iau_no"])
        sql = f"""
        SELECT sol_lon_deg
        FROM meteor
        WHERE shower_iau_no = {iau_no} AND sol_lon_deg IS NOT NULL
        ORDER BY beginning_utc_time
        LIMIT 1000
        """
        payload, provenance = query(sql)
        values = sorted(float(row["sol_lon_deg"]) % 360.0 for row in rows(payload) if finite(row.get("sol_lon_deg")))
        if not values:
            continue
        doubled = values + [value + 360.0 for value in values]
        window = max(1, int(math.ceil(0.90 * len(values))))
        best_width = min(doubled[i + window - 1] - doubled[i] for i in range(len(values)))
        leakage.append(
            {
                "iau_no": iau_no,
                "iau_code": shower.get("iau_code"),
                "sample_count": len(values),
                "circular_width_containing_90pct_deg": best_width,
                "solar_longitude_only_high_leakage": best_width <= 20.0,
                "query_sha256": provenance["sha256"],
            }
        )

    high_leakage = sum(bool(item["solar_longitude_only_high_leakage"]) for item in leakage)
    audit = {
        "endpoint": BASE,
        "aggregate_query_provenance": aggregate_provenance,
        "total_labeled_showers": len(shower_rows),
        "eligible_n_ge_200_years_ge_3": len(eligible),
        "strong_n_ge_1000_years_ge_5": len(strong),
        "eligible_showers": eligible,
        "largest_sample_audit": sample_summary,
        "sample_query_provenance": sample_provenance,
        "solar_longitude_leakage_audit": leakage,
        "high_leakage_count": high_leakage,
        "high_leakage_fraction": high_leakage / max(len(leakage), 1),
        "interpretation_rules": {
            "data_gate": "GO only if at least 20 showers have >=200 members across >=3 years and at least 10 have >=1000 across >=5 years.",
            "label_gate": "GMN shower labels are noisy teacher labels, not independent ground truth.",
            "leakage_gate": "Any later benchmark must include a solar-longitude-only baseline and solar-longitude ablation; fail if the proposed model's gain disappears.",
            "holdout_gate": "Hold out entire IAU shower codes and related complexes, never random events from the same shower.",
            "real_transfer_gate": "A later method must transfer to untouched real weak streams not used by the GMN association catalog, including ESV or another independent discovery.",
        },
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    data_go = len(eligible) >= 20 and len(strong) >= 10
    report = [
        "# Real-shower meta-learning data audit",
        "",
        f"**Data verdict:** `{'GO_TO_DESIGN' if data_go else 'DATA_NO_GO'}`",
        "",
        f"- Labeled showers returned: {len(shower_rows)}",
        f"- Eligible showers (>=200 meteors, >=3 years): {len(eligible)}",
        f"- Strong showers (>=1000 meteors, >=5 years): {len(strong)}",
        f"- Largest-shower samples with <=20 degree 90% solar-longitude width: {high_leakage}/{len(leakage)}",
        "",
        "## Methodological implication",
        "",
        "The labels are suitable only as noisy pools of real shower morphology. They are not independent truth because they were produced by an existing shower-association system. A valid method must use complete shower/complex holdouts, compare against a solar-longitude-only label-leakage baseline, and pass a real unlabeled-stream transfer test.",
        "",
        "## Next gate",
        "",
        "If the data gate passes, the next Stage-0 should compare episodic real-shower learning against matched-track, density, and labeler-proxy baselines on entirely held-out shower complexes. No GhostStream events may be used for training or tuning.",
    ]
    (OUT / "AUDIT_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "data_go": data_go,
        "total_labeled_showers": len(shower_rows),
        "eligible": len(eligible),
        "strong": len(strong),
        "high_leakage": high_leakage,
        "leakage_examined": len(leakage),
    }, indent=2))


if __name__ == "__main__":
    main()
