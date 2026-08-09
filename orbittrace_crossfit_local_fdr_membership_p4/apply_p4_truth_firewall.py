#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PARSE_HELPER_ANCHOR = '''def main() -> int:
'''
PARSE_HELPER_REPL = '''def p4_geometry_arrays(frame: Any, columns: dict[str, str]):
    ids = frame[columns["id"]].astype(str).to_numpy()
    sol = frame[columns["sol"]].to_numpy(dtype=np.float64, na_value=np.nan)
    lam = frame[columns["lam"]].to_numpy(dtype=np.float64, na_value=np.nan)
    bet = frame[columns["bet"]].to_numpy(dtype=np.float64, na_value=np.nan)
    vg = frame[columns["vg"]].to_numpy(dtype=np.float64, na_value=np.nan)
    return ids, sol, lam, bet, vg


def p4_valid_mask(sol: np.ndarray, lam: np.ndarray, bet: np.ndarray, vg: np.ndarray, support: Any) -> np.ndarray:
    valid = np.isfinite(sol) & np.isfinite(lam) & np.isfinite(bet) & np.isfinite(vg)
    valid &= (sol >= 0.0) & (sol <= 360.0) & (lam >= 0.0) & (lam <= 360.0)
    valid &= (bet >= -90.0) & (bet <= 90.0) & (vg >= 5.0) & (vg <= 75.0)
    blind = (sol >= float(support.BLIND_LOW)) & (sol <= float(support.BLIND_HIGH))
    return valid & ~blind


def p4_parse_geometry_only(support: Any, base: Any):
    scan = {year: [] for year in YEARS}
    audits = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        year = int(key[:4])
        text = support.dd.get_monthly_file_content_by_date(key)
        payload = text.encode("utf-8")
        frame = support.read_gmn_frame(text)
        columns = support.column_map(frame)
        ids, sol, lam, bet, vg = p4_geometry_arrays(frame, columns)
        keep = p4_valid_mask(sol, lam, bet, vg, support)
        accepted = duplicates = 0
        for index in np.flatnonzero(keep):
            eid = str(ids[int(index)])
            if not eid or eid in seen:
                duplicates += int(bool(eid))
                continue
            seen.add(eid)
            s = float(sol[int(index)])
            scan[year].append({
                "id": eid, "year": year, "sol": s,
                "sun_lon": float(base.wrap180(float(lam[int(index)]) - s)),
                "ecl_lat": float(bet[int(index)]), "vg": float(vg[int(index)]),
                "iau": 0, "complex_key": "HIDDEN",
            })
            accepted += 1
        audits.append({
            "key": key, "bytes": len(payload), "sha256": support.sha256_bytes(payload),
            "raw_rows": int(len(frame)), "geometry_rows_after_blind_and_dedup": accepted,
            "duplicates_removed": duplicates,
            "label_column_name_present_but_value_unread": columns["label"],
            "label_value_accessed": False,
        })
    return scan, audits, seen


def p4_parse_truth_after_freeze(support: Any, expected_ids: set[str]):
    hidden: dict[str, str] = {}
    audits = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        text = support.dd.get_monthly_file_content_by_date(key)
        frame = support.read_gmn_frame(text)
        columns = support.column_map(frame)
        ids, sol, lam, bet, vg = p4_geometry_arrays(frame, columns)
        keep = p4_valid_mask(sol, lam, bet, vg, support)
        selected = duplicates = 0
        for index in np.flatnonzero(keep):
            eid = str(ids[int(index)])
            if not eid or eid in seen:
                duplicates += int(bool(eid))
                continue
            seen.add(eid)
            require(eid in expected_ids, f"P4 truth pass added pretruth-absent event {eid}")
            # FIRST indexing of known-shower label value in P4 occurs here.
            label = support.normalize_label(frame.iloc[int(index)][columns["label"]])
            hidden[eid] = label if label else "SPORADIC"
            selected += 1
        audits.append({
            "key": key, "truth_rows": selected, "duplicates_removed": duplicates,
            "label_value_accessed_only_after_blind_and_dedup": True,
        })
    require(seen == expected_ids, f"P4 truth/pretruth event universe mismatch truth={len(seen)} pretruth={len(expected_ids)}")
    require(set(hidden) == expected_ids, "P4 truth labels missing expected IDs")
    return hidden, audits


def main() -> int:
'''

PARSE_ANCHOR = '''    scan_by_year, _, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''
PARSE_REPL = '''    scan_by_year, geometry_audits, pretruth_ids = p4_parse_geometry_only(support, base)
    hidden_labels = None
    sources = geometry_audits
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''

TRUTH_ANCHOR = '''    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''
TRUTH_REPL = '''    # FIRST known-shower label-value access: every P4 fold model, reciprocal
    # calibration decision, proposal/conflict decision and membership is frozen.
    require(all(len(x) == 64 for x in (model_sha, calibration_sha, decision_sha, membership_sha)), "P4 pretruth hashes missing before truth")
    hidden_labels, truth_audits = p4_parse_truth_after_freeze(support, pretruth_ids)
    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''

GATE_ANCHOR = '''        "membership_frozen_before_truth_evaluation": bool(membership_sha),
'''
GATE_REPL = '''        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "p4_label_values_unread_until_membership_freeze": all(a["label_value_accessed"] is False for a in geometry_audits) and all(a["label_value_accessed_only_after_blind_and_dedup"] is True for a in truth_audits),
'''

RESULT_ANCHOR = '''        "sources": sources,
'''
RESULT_REPL = '''        "sources": sources,
        "geometry_audits": geometry_audits,
        "truth_audits": truth_audits,
'''


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P4 truth-firewall anchor {label} count={count}")
    return text.replace(before, after, 1)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p4_truth_firewall.py P4_STAGE1 OUTPUT")
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")
    for before, after, label in (
        (PARSE_HELPER_ANCHOR, PARSE_HELPER_REPL, "helpers"),
        (PARSE_ANCHOR, PARSE_REPL, "geometry-only parse"),
        (TRUTH_ANCHOR, TRUTH_REPL, "post-freeze truth open"),
        (GATE_ANCHOR, GATE_REPL, "truth firewall gate"),
        (RESULT_ANCHOR, RESULT_REPL, "truth audit result"),
    ):
        text = replace_once(text, before, after, label)
    out.write_text(text, encoding="utf-8")
    compile(text, str(out), "exec")
    print("P4_TRUTH_FIREWALL=no known-shower label value indexed before model/calibration/decision/membership freeze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
