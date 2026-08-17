#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

YEARS = (2018, 2019)
BLIND = (20.0, 55.0)
ARCHIVE_SHA = "c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4"
README_SHA = "74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf"
DATA_BASENAME = "nasfn_2013-2019_data.txt"
README_BASENAME = "nasfn_2013-2019_readme.txt"
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
FIELDS = (
    "time", "jd", "slon", "n", "Qstar", "sat", "lat1", "dlat1", "lon1", "dlon1", "h1", "dh1",
    "lat2", "dlat2", "lon2", "dlon2", "h2", "dh2", "dur", "mag", "L_int", "eta_p", "deta_p",
    "rho_p", "drho_p", "v_p", "dv_p", "alp_g", "dalp_g", "del_g", "ddel_g", "v_g", "dv_g",
    "lam_g", "dlam_g", "bet_g", "dbet_g", "q", "e", "incl", "omega", "anode", "shw", "T_j",
)
IDX = {name: i for i, name in enumerate(FIELDS)}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def parse_float(token: str) -> float | None:
    try:
        x = float(token)
    except Exception:
        return None
    return x if math.isfinite(x) else None


def header_or_record(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if tokens[0].lower() != "time":
        return False
    req(len(tokens) >= len(FIELDS), "ASFN header shorter than readme field list")
    got = tuple(tokens[:len(FIELDS)])
    req(tuple(x.lower() for x in got) == tuple(x.lower() for x in FIELDS), f"ASFN header order changed: {got}")
    return True


def iter_member_lines(z: zipfile.ZipFile, member: str):
    with z.open(member, "r") as raw:
        for raw_line in raw:
            yield raw_line.decode("utf-8", errors="strict").strip()


def first_pass(archive: Path) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    req(sha_file(archive) == ARCHIVE_SHA, "ASFN archive SHA-256 changed")
    events: list[dict[str, Any]] = []
    stats = Counter()
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        readmes = [i for i in infos if Path(i.filename).name == README_BASENAME]
        data = [i for i in infos if Path(i.filename).name == DATA_BASENAME]
        req(len(readmes) == 1 and len(data) == 1, "ASFN archive members changed")
        req(hashlib.sha256(z.read(readmes[0].filename)).hexdigest() == README_SHA, "ASFN readme changed")
        data_member = data[0].filename
        physical_index = 0
        header_seen = False
        for line in iter_member_lines(z, data_member):
            if not line:
                continue
            tokens = line.split()
            if not header_seen and header_or_record(tokens):
                header_seen = True
                stats["header_lines"] += 1
                continue
            physical_index += 1
            stats["physical_records"] += 1
            req(len(tokens) >= len(FIELDS), f"ASFN record {physical_index} has {len(tokens)} fields, expected >= {len(FIELDS)}")
            time_token = tokens[IDX["time"]]
            req(len(time_token) >= 4 and time_token[:4].isdigit(), f"invalid ASFN time at record {physical_index}")
            year = int(time_token[:4])
            slon = parse_float(tokens[IDX["slon"]])
            if slon is None:
                stats["invalid_slon"] += 1
                continue
            slon %= 360.0
            if year not in YEARS:
                stats["nonvalidation_year"] += 1
                continue
            stats[f"year_{year}_before_blind"] += 1
            if BLIND[0] <= slon <= BLIND[1]:
                stats[f"year_{year}_blind_excluded"] += 1
                continue
            # Only now may the recurrent-EOM scientific channels be decoded.
            lam_g = parse_float(tokens[IDX["lam_g"]])
            bet_g = parse_float(tokens[IDX["bet_g"]])
            vg = parse_float(tokens[IDX["v_g"]])
            if lam_g is None or bet_g is None or vg is None or vg <= 0.0:
                stats[f"year_{year}_no_geocentric_solution"] += 1
                continue
            eid = f"ASFN:{physical_index}"
            lon_sc = (lam_g - slon) % 360.0
            events.append({
                "id": eid,
                "row_index": physical_index,
                "year": year,
                "sol": float(slon),
                "lon": float(lon_sc),
                "lat": float(bet_g),
                "vg": float(vg),
            })
            stats[f"year_{year}_eligible"] += 1
        req(physical_index > 0, "ASFN data member contained no records")
    req(events, "no eligible ASFN validation events")
    req(len({e["id"] for e in events}) == len(events), "duplicate deterministic ASFN event ID")
    req(all(e["year"] in YEARS for e in events), "wrong ASFN year reached model")
    req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in events), "protected ASFN event reached model")
    provenance = {
        "archive_sha256": ARCHIVE_SHA,
        "readme_sha256": README_SHA,
        "data_member": data_member,
        "data_member_uncompressed_bytes": int(data[0].file_size),
        "physical_record_count": int(physical_index),
        "header_seen": bool(header_seen),
        "nonvalidation_year_scientific_fields_decoded": False,
        "protected_region_radiant_speed_or_label_decoded": False,
        "shw_accessed": False,
    }
    return events, {k: int(v) for k, v in sorted(stats.items())}, provenance


def geo_matrix(events: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([e["sol"] for e in events], dtype=float))
    lon = np.radians(np.asarray([e["lon"] for e in events], dtype=float))
    lat = np.radians(np.asarray([e["lat"] for e in events], dtype=float))
    vg = np.asarray([e["vg"] for e in events], dtype=float)
    return np.column_stack((
        np.cos(sol), np.sin(sol),
        np.sin(lon) * np.cos(lat), np.cos(lon) * np.cos(lat), np.sin(lat),
        vg / 72.0,
    ))


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(
        tuple(np.flatnonzero(labels == lab).tolist())
        for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    ))


def member_hash(prefix: str, members: tuple[str, ...]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def build_candidates(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    X = geo_matrix(events)
    years = np.asarray([e["year"] for e in events], dtype=np.int64)
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    vanilla_labels = eom_labels(tree, ordinary)
    req(canonical_partition(model.labels_) == canonical_partition(vanilla_labels), "ASFN vanilla extraction mismatch")
    vanilla_nodes = selected_eom_nodes(tree, ordinary)
    recurrent, annual = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)

    def families(labels: np.ndarray, nodes: tuple[int, ...], recurrent_mode: bool) -> list[dict[str, Any]]:
        positive = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
        req(positive == list(range(len(nodes))), "ASFN compact-label/node mapping changed")
        out = []
        for lab, node in enumerate(nodes):
            idx = np.flatnonzero(labels == lab)
            members = tuple(sorted(events[int(i)]["id"] for i in idx))
            req(len(members) >= MIN_CLUSTER_SIZE, f"ASFN subminimum selected cluster {node}")
            row = {
                "family_id": member_hash("ASFN-REOM1" if recurrent_mode else "ASFN-HDB", members),
                "node_id": int(node),
                "event_ids": list(members),
                "member_count": len(members),
                "ordinary_stability": float(ordinary[float(node)]),
            }
            if recurrent_mode:
                row["recurrent_stability"] = float(recurrent[float(node)])
            out.append(row)
        if recurrent_mode:
            out.sort(key=lambda f: (-f["recurrent_stability"], -f["ordinary_stability"], -f["member_count"], f["family_id"]))
        else:
            out.sort(key=lambda f: (-f["ordinary_stability"], -f["member_count"], f["family_id"]))
        return out

    vanilla = families(vanilla_labels, vanilla_nodes, False)
    successor = families(recurrent_labels, recurrent_nodes, True)
    tree_hash = hashlib.sha256(tree.tobytes()).hexdigest()
    diag = {
        "condensed_tree_sha256": tree_hash,
        "vanilla_selected_nodes": list(vanilla_nodes),
        "recurrent_selected_nodes": list(recurrent_nodes),
        "mechanism_active": vanilla_nodes != recurrent_nodes,
        "vanilla_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in vanilla).encode()).hexdigest(),
        "recurrent_order_sha256": hashlib.sha256("\n".join(f["family_id"] for f in successor).encode()).hexdigest(),
        "annual_recurrent_stability_sha256": sha_json({str(k): list(v) for k, v in sorted(annual.items())}),
    }
    return vanilla, successor, diag


def second_pass_labels(archive: Path, retained: list[dict[str, Any]]) -> dict[str, str]:
    wanted = {int(e["row_index"]): e for e in retained}
    labels: dict[str, str] = {}
    with zipfile.ZipFile(archive) as z:
        data = [i for i in z.infolist() if Path(i.filename).name == DATA_BASENAME]
        req(len(data) == 1, "ASFN data member changed on label pass")
        physical_index = 0
        header_seen = False
        for line in iter_member_lines(z, data[0].filename):
            if not line:
                continue
            tokens = line.split()
            if not header_seen and header_or_record(tokens):
                header_seen = True
                continue
            physical_index += 1
            if physical_index not in wanted:
                continue
            req(len(tokens) >= len(FIELDS), f"ASFN label record {physical_index} malformed")
            # Recheck only the already-authorized time/slon selectors before touching shw.
            year = int(tokens[IDX["time"]][:4])
            slon = float(tokens[IDX["slon"]]) % 360.0
            req(year in YEARS and not (BLIND[0] <= slon <= BLIND[1]), "label pass selector mismatch")
            code = tokens[IDX["shw"]].strip()
            labels[wanted[physical_index]["id"]] = "SPORADIC" if code in {"", "..."} else code
    req(set(labels) == {e["id"] for e in retained}, "ASFN label pass did not recover exact retained ID set")
    return labels


def eligible_labels(labels: dict[str, str], annual_ids: set[str]) -> dict[str, int]:
    c = Counter(v for eid, v in labels.items() if eid in annual_ids and v != "SPORADIC")
    return {label: n for label, n in c.items() if n >= 4}


def truth(f: dict[str, Any], labels: dict[str, str], eligible: dict[str, int], annual_ids: set[str]) -> dict[str, Any]:
    ids = [str(x) for x in f["event_ids"] if str(x) in annual_ids]
    counts = Counter(labels.get(eid, "SPORADIC") for eid in ids)
    rows = []
    for label, total in eligible.items():
        ov = int(counts.get(label, 0))
        if ov <= 0:
            continue
        p = ov / max(len(ids), 1)
        r = ov / total
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        rows.append((f1, p, ov, label, r))
    if not rows:
        non = counts.copy(); non.pop("SPORADIC", None)
        dominant = max(non.values(), default=0) / max(len(ids), 1)
        return {"positive": False, "best_label": None, "dominant_precision": float(dominant)}
    f1, p, ov, label, r = max(rows, key=lambda x: (x[0], x[1], x[2], x[3]))
    non = counts.copy(); non.pop("SPORADIC", None)
    dominant = max(non.values(), default=0) / max(len(ids), 1)
    return {
        "positive": bool(p >= 0.5 and ov >= 4),
        "best_label": label,
        "f1": float(f1), "precision": float(p), "recall": float(r), "overlap": ov,
        "dominant_precision": float(dominant),
    }


def metrics(fams: list[dict[str, Any]], labels: dict[str, str], annual_ids: set[str]) -> dict[str, Any]:
    eligible = eligible_labels(labels, annual_ids)
    first: dict[str, int | None] = {label: None for label in eligible}
    fragments: Counter[str] = Counter()
    top_prec = []
    for rank, f in enumerate(fams, 1):
        t = truth(f, labels, eligible, annual_ids)
        if rank <= 100:
            top_prec.append(float(t["dominant_precision"]))
        if t["positive"] and t["best_label"] in eligible:
            label = str(t["best_label"])
            fragments[label] += int(rank <= 500)
            if first[label] is None:
                first[label] = rank
    represented = [label for label, r in first.items() if r is not None]
    frag = [fragments[label] for label in represented if first[label] is not None and first[label] <= 500]
    return {
        "eligible_labels": len(eligible),
        "qualified_matches": len(represented),
        "recovered_at_25": sum(r is not None and r <= 25 for r in first.values()),
        "recovered_at_50": sum(r is not None and r <= 50 for r in first.values()),
        "recovered_at_100": sum(r is not None and r <= 100 for r in first.values()),
        "recovered_at_500": sum(r is not None and r <= 500 for r in first.values()),
        "top100_dominant_precision": float(np.mean(top_prec)) if top_prec else 0.0,
        "mrr": float(np.mean([1.0 / r for r in first.values() if r is not None])) if represented else 0.0,
        "fragmentation_median_top500": float(np.median(frag)) if frag else 0.0,
        "first_rank_by_label": first,
    }


def annual_gate(parent: dict[str, Any], successor: dict[str, Any]) -> dict[str, bool]:
    return {
        "recovered_at_50_not_lower": int(successor["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(successor["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": float(successor["top100_dominant_precision"]) >= float(parent["top100_dominant_precision"]),
        "mrr_not_lower": float(successor["mrr"]) >= float(parent["mrr"]),
        "fragmentation_not_higher": float(successor["fragmentation_median_top500"]) <= float(parent["fragmentation_median_top500"]),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)

    events, parse_stats, provenance = first_pass(a.archive)
    vanilla, successor, diag = build_candidates(events)
    prelabel = {
        "scientific_role": "PRISTINE_ASFN_2018_2019_PRELABEL_ONLY",
        "events": events,
        "parse_stats": parse_stats,
        "provenance": provenance,
        "vanilla_candidates": vanilla,
        "recurrent_candidates": successor,
        "hierarchy": diag,
        "blind_exclusion": list(BLIND),
        "shw_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2020_2021_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECURRENT_EOM_ASFN_2018_2019_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha_file(prelabel_path)

    # Only after the exact candidate universe/order is on disk do external ASFN shower codes enter.
    labels = second_pass_labels(a.archive, events)
    ids_by_year = {y: {e["id"] for e in events if e["year"] == y} for y in YEARS}
    parent_metrics = {str(y): metrics(vanilla, labels, ids_by_year[y]) for y in YEARS}
    successor_metrics = {str(y): metrics(successor, labels, ids_by_year[y]) for y in YEARS}
    gates = {str(y): annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(successor_metrics[str(y)]["recovered_at_100"] > parent_metrics[str(y)]["recovered_at_100"] for y in YEARS)
    passed = bool(strict_100 and diag["mechanism_active"] and all(all(g.values()) for g in gates.values()))
    verdict = "PASS_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION" if passed else "FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION"

    label_counts = {
        str(y): {
            "sporadic": sum(labels[eid] == "SPORADIC" for eid in ids_by_year[y]),
            "associated": sum(labels[eid] != "SPORADIC" for eid in ids_by_year[y]),
            "eligible_reference_showers": len(eligible_labels(labels, ids_by_year[y])),
        }
        for y in YEARS
    }
    result = {
        "verdict": verdict,
        "scientific_role": "PRISTINE_CROSS_SURVEY_ASFN_2018_2019_VALIDATION",
        "reference_label_role": "PREEXISTING_ASFN_SHOWER_ASSOCIATIONS_RELATIVE_METHOD_COMPARISON_ONLY",
        "prelabel_sha256": prelabel_sha,
        "archive_sha256": ARCHIVE_SHA,
        "events_total": len(events),
        "events_by_year": {str(y): len(ids_by_year[y]) for y in YEARS},
        "parse_stats": parse_stats,
        "label_counts": label_counts,
        "vanilla_candidate_count": len(vanilla),
        "recurrent_candidate_count": len(successor),
        "mechanism_active": bool(diag["mechanism_active"]),
        "strict_recovered_at_100_improvement_some_year": bool(strict_100),
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": gates,
        "frozen_hdbscan": {
            "representation": "GEO6_from_slON_and_sun_centered_geocentric_radiant_and_vg",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
        },
        "blind_exclusion": list(BLIND),
        "validation_years": list(YEARS),
        "nonvalidation_year_scientific_fields_decoded": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "gmn_2020_2021_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "RECURRENT_EOM_ASFN_2018_2019_VALIDATION.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "events_by_year": result["events_by_year"],
        "label_counts": label_counts,
        "vanilla_candidates": len(vanilla),
        "recurrent_candidates": len(successor),
        "parent": {y: {k:v for k,v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k:v for k,v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
