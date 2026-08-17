#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

BLIND = (20.0, 55.0)
YEARS = (2013, 2014)
PAIRS = ("hdbscan", "sugar", "dsh")
MATCHED_FREEZE_SHA256 = "690056f48569e1b5049974d970ce736f5af7fc90b2331edb2d72c480979c3be3"
DIRECT_SHA = {
    2013: "0ac3e364466451e2eb4ebccc529bf24b51b6051a0277c9f3b9ba6da4363b1daf",
    2014: "7f723abf6a9890fc36e5fb4d477ef7880e5084eaa07248d387a63442c94c9c51",
}
EXPECTED_BUDGETS = {("sugar", 2013): 34, ("sugar", 2014): 46, ("dsh", 2013): 41, ("dsh", 2014): 47}
FORBIDDEN_FIELDS = {"label", "shower", "truth", "known_shower", "native_background", "sporadic"}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def physcore_families(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fams = payload["families"]
    req(len(fams) == int(payload["family_count"]), "PhysCore family count mismatch")
    out = []
    for i, f in enumerate(fams, 1):
        req(int(f["rank"]) == i, "PhysCore rank changed")
        ids = [str(x) for x in f["event_ids"]]
        out.append({
            "family_id": str(f["family_id"]),
            "event_ids": ids,
            "member_count": len(ids),
            "source": "physcore",
        })
    return out


def direct_prefix_equal(transfer: dict[str, Any], direct: dict[str, Any]) -> bool:
    a = physcore_families(transfer)
    b = physcore_families(direct)
    return len(a) == len(b) and all(x["family_id"] == y["family_id"] and x["event_ids"] == y["event_ids"] for x, y in zip(a, b))


def event_rows(rows: list[dict[str, Any]], residual_ids: set[str], year: int) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        rid = str(row["id"])
        req(int(row["year"]) == year, f"row year mismatch {rid}")
        req(not (BLIND[0] <= float(row["sol"]) <= BLIND[1]), f"protected event reached residual stage: {rid}")
        lower = {str(k).lower() for k in row}
        req(not (FORBIDDEN_FIELDS & lower), f"truth-bearing field reached candidate generation: {rid}")
        if rid in residual_ids:
            out.append({
                "id": rid,
                "year": year,
                "sol": float(row["sol"]),
                "lon": float(row["sun_lon"]),
                "lat": float(row["ecl_lat"]),
                "vg": float(row["vg"]),
            })
    req({r["id"] for r in out} == residual_ids, "residual row projection lost IDs")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matched-pretruth", type=Path, required=True)
    ap.add_argument("--direct-pretruth", type=Path, required=True)
    ap.add_argument("--rows", type=Path, required=True)
    ap.add_argument("--topomodal-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    matched_freeze = a.matched_pretruth / "freeze" / "PRETRUTH_FREEZE.json"
    req(sha(matched_freeze) == MATCHED_FREEZE_SHA256, "matched-literature pretruth freeze drift")
    freeze = load(matched_freeze)
    req(freeze["schema"] == "ORBITTRACE_PHYSCORE_MATCHED_LITERATURE_V1_PRETRUTH_FREEZE", "wrong matched freeze schema")
    req(freeze["pretruth_outputs_frozen"] is True and freeze["truth_accessed_before_freeze"] is False, "bad matched freeze")
    req(freeze["target_information_access"] is False and freeze["target_region_events_accessed"] is False, "target access in matched freeze")
    req(freeze["maarsy_scientific_access"] is False and freeze["dms_scientific_access"] is False, "forbidden survey access in matched freeze")
    panel_meta = {(str(x["pair"]), int(x["year"])): x for x in freeze["panels"]}
    req(set(panel_meta) == set(EXPECTED_BUDGETS), "matched panel set changed")
    req(all(int(panel_meta[k]["literature_family_count"]) == v for k, v in EXPECTED_BUDGETS.items()), "literature budgets changed")

    for e in freeze["transfer_equivalence"]:
        y = int(e["year"])
        req(e["exact_membership_equivalence"] is True, f"historical transfer equivalence failed {y}")
        req(str(e["direct_candidate_sha256"]) == DIRECT_SHA[y], f"direct identity changed {y}")

    tm = load_module(a.topomodal_source, "frozen_residual_topomodal")
    summaries: list[dict[str, Any]] = []
    all_capacity = True
    prefix_ok = True

    for pair in PAIRS:
        for year in YEARS:
            row_path = a.rows / f"{pair}_{year}.json"
            rows = load(row_path)
            req(isinstance(rows, list) and rows, f"missing rows {pair} {year}")
            ids = [str(r["id"]) for r in rows]
            req(len(ids) == len(set(ids)), f"duplicate row IDs {pair} {year}")
            req(all(not (BLIND[0] <= float(r["sol"]) <= BLIND[1]) for r in rows), f"protected rows in {pair} {year}")

            phys_path = a.matched_pretruth / "generated" / f"physcore_{pair}_{year}" / f"physcore_{pair}_{year}.json"
            phys_payload = load(phys_path)
            phys = physcore_families(phys_payload)
            req(int(phys_payload["year"]) == year, "PhysCore year mismatch")
            req(bool(phys_payload["truth_accessed"]) is False, "truth reached PhysCore pretruth")
            if pair in {"sugar", "dsh"}:
                meta = panel_meta[(pair, year)]
                req(sha(row_path) == str(meta["pairwise_rows_json_sha256"]), f"row hash drift {pair} {year}")
                req(sha(phys_path) == str(meta["physcore_output_sha256"]), f"PhysCore hash drift {pair} {year}")
                req(len(phys) == int(meta["physcore_family_count"]), f"PhysCore count drift {pair} {year}")
            else:
                direct_path = a.direct_pretruth / "pretruth" / f"physcore_{year}.json"
                req(sha(direct_path) == DIRECT_SHA[year], f"direct PhysCore file drift {year}")
                eq = direct_prefix_equal(phys_payload, load(direct_path))
                prefix_ok = prefix_ok and eq
                req(eq, f"direct PhysCore prefix mismatch {year}")

            universe = set(ids)
            accepted: set[str] = set()
            for f in phys:
                fs = set(f["event_ids"])
                req(fs <= universe, f"PhysCore family leaves row universe {pair} {year}")
                accepted.update(fs)
            residual_ids = universe - accepted
            residual_events = event_rows(rows, residual_ids, year)
            residual_tm, tm_diag = tm.topomodal_ranked(residual_events)

            final: list[dict[str, Any]] = []
            for f in phys:
                final.append(dict(f))
            for f in residual_tm:
                fs = set(map(str, f["event_ids"]))
                req(fs <= residual_ids, f"TopoModal family leaves residual universe {pair} {year}")
                req(fs.isdisjoint(accepted), f"TopoModal/PhysCore overlap {pair} {year}")
                row = dict(f)
                row["event_ids"] = [str(x) for x in row["event_ids"]]
                row["source"] = "residual_topomodal"
                final.append(row)
            for rank, f in enumerate(final, 1):
                f["rank"] = rank
            req(final[:len(phys)] and all(final[i]["family_id"] == phys[i]["family_id"] and final[i]["event_ids"] == phys[i]["event_ids"] for i in range(len(phys))), "PhysCore prefix changed after concatenation")

            budget = EXPECTED_BUDGETS.get((pair, year))
            capacity_ok = True if budget is None else len(final) >= budget
            all_capacity = all_capacity and capacity_ok
            panel_out = {
                "schema": "ORBITTRACE_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH_PANEL",
                "pair": pair,
                "year": year,
                "row_count": len(rows),
                "physcore_family_count": len(phys),
                "physcore_accepted_event_count": len(accepted),
                "residual_event_count": len(residual_ids),
                "residual_topomodal_family_count": len(residual_tm),
                "successor_family_count": len(final),
                "literature_budget": budget,
                "capacity_ok": bool(capacity_ok),
                "topomodal_diagnostics": tm_diag,
                "families": final,
                "truth_accessed": False,
                "target_information_access": False,
                "target_region_events_accessed": False,
                "maarsy_scientific_access": False,
                "dms_scientific_access": False,
            }
            out_path = a.output / "panels" / f"successor_{pair}_{year}.json"
            out_sha = dump(out_path, panel_out)
            summaries.append({
                "pair": pair,
                "year": year,
                "row_count": len(rows),
                "physcore_family_count": len(phys),
                "accepted_event_count": len(accepted),
                "residual_event_count": len(residual_ids),
                "residual_topomodal_family_count": len(residual_tm),
                "successor_family_count": len(final),
                "literature_budget": budget,
                "capacity_ok": bool(capacity_ok),
                "output_sha256": out_sha,
            })
            print(f"[residual-pretruth] {pair} {year}: U={len(rows)} A={len(accepted)} R={len(residual_ids)} phys={len(phys)} tm={len(residual_tm)} total={len(final)} budget={budget}", flush=True)

    activation = bool(prefix_ok and all_capacity)
    verdict = "PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH" if activation else "FAIL_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH"
    out = {
        "schema": "ORBITTRACE_PHYSCORE_RESIDUAL_TOPOMODAL_V1_PRETRUTH_FREEZE",
        "scientific_role": "PRETRUTH_STRUCTURAL_ACTIVATION",
        "verdict": verdict,
        "activation_gates_pass": activation,
        "direct_physcore_prefix_equivalence": bool(prefix_ok),
        "all_literature_capacity_gates_pass": bool(all_capacity),
        "matched_pretruth_freeze_sha256": sha(matched_freeze),
        "frozen_topomodal_git_blob": "752df8212ce601227f6e9170b0fe994ba06b515d",
        "panels": summaries,
        "blind_exclusion": list(BLIND),
        "truth_accessed_before_freeze": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_sha = dump(a.output / "PRETRUTH_FREEZE.json", out)
    print(json.dumps({"verdict": verdict, "pretruth_sha256": result_sha, "panels": summaries}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
