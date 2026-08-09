#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p3_patch_v1", HERE / "apply_p3_patch.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load P3 base patch")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# v1 now contains the exact preregistered P3 scientific transform and all
# cross-fit/decision integrity gates.  v2 adds only a two-pass label-dataflow
# firewall so no known-shower label value is indexed before every P3 pretruth
# payload is durably frozen.  It does not override any v1 scientific anchor.

TRUTH_HELPER_ANCHOR = '''def main() -> int:
'''
TRUTH_HELPER_REPL = '''def p3_geometry_arrays(frame: Any, columns: dict[str, str]):
    ids = frame[columns["id"]].astype(str).to_numpy()
    sol = frame[columns["sol"]].to_numpy(dtype=np.float64, na_value=np.nan)
    lam = frame[columns["lam"]].to_numpy(dtype=np.float64, na_value=np.nan)
    bet = frame[columns["bet"]].to_numpy(dtype=np.float64, na_value=np.nan)
    vg = frame[columns["vg"]].to_numpy(dtype=np.float64, na_value=np.nan)
    return ids, sol, lam, bet, vg


def p3_valid_mask(sol: np.ndarray, lam: np.ndarray, bet: np.ndarray, vg: np.ndarray, support: Any) -> np.ndarray:
    valid = np.isfinite(sol) & np.isfinite(lam) & np.isfinite(bet) & np.isfinite(vg)
    valid &= (sol >= 0.0) & (sol <= 360.0) & (lam >= 0.0) & (lam <= 360.0)
    valid &= (bet >= -90.0) & (bet <= 90.0) & (vg >= 5.0) & (vg <= 75.0)
    blind = (sol >= float(support.BLIND_LOW)) & (sol <= float(support.BLIND_HIGH))
    return valid & ~blind


def p3_parse_geometry_only(support: Any, base: Any):
    scan = {year: [] for year in YEARS}
    audits = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        year = int(key[:4])
        text = support.dd.get_monthly_file_content_by_date(key)
        payload = text.encode("utf-8")
        frame = support.read_gmn_frame(text)
        columns = support.column_map(frame)
        ids, sol, lam, bet, vg = p3_geometry_arrays(frame, columns)
        keep = p3_valid_mask(sol, lam, bet, vg, support)
        accepted = duplicates = 0
        for index in np.flatnonzero(keep):
            eid = str(ids[int(index)])
            if not eid or eid in seen:
                duplicates += int(bool(eid))
                continue
            seen.add(eid)
            s = float(sol[int(index)])
            scan[year].append({
                "id": eid,
                "year": year,
                "sol": s,
                "sun_lon": float(base.wrap180(float(lam[int(index)]) - s)),
                "ecl_lat": float(bet[int(index)]),
                "vg": float(vg[int(index)]),
                "iau": 0,
                "complex_key": "HIDDEN",
            })
            accepted += 1
        audits.append({
            "key": key,
            "bytes": len(payload),
            "sha256": support.sha256_bytes(payload),
            "raw_rows": int(len(frame)),
            "geometry_rows_after_blind_and_dedup": accepted,
            "duplicates_removed": duplicates,
            "columns": {name: columns[name] for name in ("id", "sol", "lam", "bet", "vg")},
            "label_column_name_present_but_value_unread": columns["label"],
            "label_value_accessed": False,
        })
    return scan, audits, seen


def p3_parse_truth_after_freeze(support: Any, expected_ids: set[str]):
    hidden: dict[str, str] = {}
    audits = []
    seen: set[str] = set()
    for key in MONTH_KEYS:
        text = support.dd.get_monthly_file_content_by_date(key)
        frame = support.read_gmn_frame(text)
        columns = support.column_map(frame)
        ids, sol, lam, bet, vg = p3_geometry_arrays(frame, columns)
        keep = p3_valid_mask(sol, lam, bet, vg, support)
        selected = duplicates = 0
        for index in np.flatnonzero(keep):
            eid = str(ids[int(index)])
            if not eid or eid in seen:
                duplicates += int(bool(eid))
                continue
            seen.add(eid)
            require(eid in expected_ids, f"P3 truth pass added pretruth-absent event {eid}")
            # FIRST indexing of a known-shower label value occurs here.
            label = support.normalize_label(frame.iloc[int(index)][columns["label"]])
            hidden[eid] = label if label else "SPORADIC"
            selected += 1
        audits.append({
            "key": key,
            "truth_rows": selected,
            "duplicates_removed": duplicates,
            "label_value_accessed_only_after_blind_and_dedup": True,
        })
    require(seen == expected_ids, f"P3 truth/pretruth event universe mismatch truth={len(seen)} pretruth={len(expected_ids)}")
    require(set(hidden) == expected_ids, "P3 truth labels missing expected IDs")
    return hidden, audits


def main() -> int:
'''

PARSE_ANCHOR = '''    scan_by_year, _, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''
PARSE_REPL = '''    scan_by_year, geometry_audits, pretruth_ids = p3_parse_geometry_only(support, base)
    hidden_labels = None
    sources = geometry_audits
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''

TRUTH_OPEN_ANCHOR = '''    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''
TRUTH_OPEN_REPL = '''    # FIRST known-shower label-value access in P3: cross-fit gates, final model,
    # candidate/conflict decisions and complete memberships are already frozen.
    require(
        len(crossfit_sha) == 64 and len(model_sha) == 64 and len(membership_sha) == 64 and len(decision_sha) == 64,
        "P3 pretruth hashes missing before truth",
    )
    hidden_labels, truth_audits = p3_parse_truth_after_freeze(support, pretruth_ids)
    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''

RESULT_AUDIT_ANCHOR = '''        "direction_audits": direction_audits,
'''
RESULT_AUDIT_REPL = '''        "geometry_audits": geometry_audits,
        "truth_audits": truth_audits,
        "direction_audits": direction_audits,
'''

GATE_ANCHOR = '''        "p3_decisions_frozen_before_truth": len(decision_sha) == 64,
'''
GATE_REPL = '''        "p3_decisions_frozen_before_truth": len(decision_sha) == 64,
        "p3_label_values_unread_until_membership_freeze": all(a["label_value_accessed"] is False for a in geometry_audits) and all(a["label_value_accessed_only_after_blind_and_dedup"] is True for a in truth_audits),
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p3_patch_v2.py CANONICAL_P2 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    stage1 = output.with_suffix(output.suffix + ".stage1")
    old_argv = sys.argv
    sys.argv = [str(HERE / "apply_p3_patch.py"), str(source), str(stage1)]
    try:
        m.main()
    finally:
        sys.argv = old_argv
    text = stage1.read_text(encoding="utf-8")
    for before, after, label in (
        (TRUTH_HELPER_ANCHOR, TRUTH_HELPER_REPL, "truth helper insertion"),
        (PARSE_ANCHOR, PARSE_REPL, "geometry-only parser"),
        (TRUTH_OPEN_ANCHOR, TRUTH_OPEN_REPL, "post-freeze truth opening"),
        (RESULT_AUDIT_ANCHOR, RESULT_AUDIT_REPL, "truth firewall audit payload"),
        (GATE_ANCHOR, GATE_REPL, "truth dataflow integrity gate"),
    ):
        text = m.replace_once(text, before, after, label)
    output.write_text(text, encoding="utf-8")
    stage1.unlink()
    print(f"P3_V2_OUTPUT_SHA256={m.digest(text.encode('utf-8'))}")
    print("P3_V2_TRUTH_FIREWALL=no known-shower label value indexed before crossfit/model/decision/membership freeze")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
