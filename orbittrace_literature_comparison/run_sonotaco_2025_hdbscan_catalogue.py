#!/usr/bin/env python3
"""Frozen Peña-Asensio–Ferrari HDBSCAN catalogue transfer on SonotaCo 2025."""
from __future__ import annotations

import argparse, base64, csv, gzip, hashlib, io, json, sys, types, zipfile
from collections import Counter
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
import sklearn
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score

import literature_comparators as lit

YEAR = 2025
CORPUS = "sonotaco-2025-native"
MEMBER = "025a/_U2_20250101_S.csv"
ARCHIVE_SHA = "f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52"
MEMBER_SHA = "30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7"
BASE_SHA = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"
ADAPTER_SHA = "5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518"
HDBSCAN_VERSION = "0.8.40"
SKLEARN_VERSION = "1.5.2"
MIN_CLUSTER_SIZE = 100
SILHOUETTE_SEED = 20250806
SILHOUETTE_MAX = 10000
SPORADIC = "SPORADIC"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--audit", required=True, type=Path)
    p.add_argument("--baseline-payload", required=True, type=Path)
    p.add_argument("--adapter-parts", required=True, type=Path)
    p.add_argument("--protocol", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    return p.parse_args()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_file(path: Path) -> bytes:
    return gzip.decompress(base64.b64decode("".join(path.read_text().split()), validate=True))


def decode_parts(path: Path) -> bytes:
    parts = sorted(path.glob("part*.b64"))
    if [p.name for p in parts] != ["part00.b64"]:
        raise RuntimeError(f"unexpected adapter parts: {[p.name for p in parts]}")
    return gzip.decompress(base64.b64decode("".join("".join(p.read_text().split()) for p in parts), validate=True))


def module(name: str, source: bytes, expected: str) -> types.ModuleType:
    if sha(source) != expected:
        raise RuntimeError(f"{name} source hash mismatch")
    m = types.ModuleType(name)
    m.__file__ = name + ".py"
    sys.modules[name] = m
    exec(compile(source, m.__file__, "exec"), m.__dict__)
    return m


def number(value: str) -> float:
    result = float(value.strip())
    if not np.isfinite(result):
        raise ValueError(value)
    return result


def quality_sidecars(archive: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = archive.read_bytes()
    if sha(payload) != ARCHIVE_SHA:
        raise RuntimeError("archive hash mismatch")
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        member = zf.read(MEMBER)
    if sha(member) != MEMBER_SHA:
        raise RuntimeError("member hash mismatch")
    rows = csv.reader(io.StringIO(member.decode("utf-8-sig")))
    header = [x.strip() for x in next(rows)]
    ix = {x: i for i, x in enumerate(header)}
    required = {"vg(km/s)", "vg sd(km/s)", "q(AU)", "e", "Qc(deg)", "Shower"}
    if not required <= set(ix):
        raise RuntimeError(f"missing fields: {sorted(required-set(ix))}")
    out, malformed, invalid = {}, 0, 0
    for i, row in enumerate(rows):
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        if len(row) != len(header):
            malformed += 1
            continue
        try:
            vg = number(row[ix["vg(km/s)"]])
            rec = {
                "vg_sd": number(row[ix["vg sd(km/s)"]]),
                "q": number(row[ix["q(AU)"]]),
                "e": number(row[ix["e"]]),
                "qc": number(row[ix["Qc(deg)"]]),
                "raw_shower": row[ix["Shower"]].strip(),
            }
        except (ValueError, IndexError):
            invalid += 1
            continue
        rec["quality"] = bool(
            rec["qc"] >= 15 and vg > 0 and 0 <= rec["vg_sd"] / vg <= 0.10
            and 0 <= rec["e"] <= 1 and 0 < rec["q"] <= 1
        )
        out[f"SNM2025:{i}"] = rec
    return out, {
        "archive_sha256": sha(payload), "member_sha256": sha(member),
        "rows": len(out), "malformed": malformed, "invalid_numeric": invalid,
        "mapping": {"convergence_angle": "Qc(deg)", "velocity_error": "vg sd / vg"},
    }


def records(labeled: list[dict[str, Any]], sporadic: list[dict[str, Any]], side: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out, missing, seen = [], [], set()
    for events, labeler in ((labeled, lambda e: str(e["shower"])), (sporadic, lambda e: SPORADIC)):
        for event in events:
            event_id = str(event["id"])
            if event_id in seen:
                raise RuntimeError(f"duplicate event id {event_id}")
            seen.add(event_id)
            if event_id not in side:
                missing.append(event_id)
                continue
            out.append({
                "id": event_id, "label": labeler(event), "sol": float(event["sol"]),
                "sun_lon": float(event["sun_lon"]), "ecl_lat": float(event["ecl_lat"]),
                "vg": float(event["vg"]), **side[event_id],
            })
    if missing:
        raise RuntimeError(f"missing sidecars for {len(missing)} events; first={missing[:5]}")
    return out


def features(rows: list[dict[str, Any]]) -> np.ndarray:
    return lit.sugar_feature_matrix_from_arrays(
        [r["sol"] for r in rows], [r["sun_lon"] for r in rows],
        [r["ecl_lat"] for r in rows], [r["vg"] for r in rows],
    )


def silhouette(x: np.ndarray, y: np.ndarray, include_noise: bool) -> dict[str, Any]:
    mask = np.ones(len(y), bool) if include_noise else y >= 0
    x, y = x[mask], y[mask]
    unique = np.unique(y)
    if len(unique) < 2 or len(unique) >= len(y):
        return {"value": None, "sample_size": 0, "categories": len(unique)}
    n = min(SILHOUETTE_MAX, len(y))
    value = silhouette_score(x, y, sample_size=n if n < len(y) else None, random_state=SILHOUETTE_SEED)
    return {"value": float(value), "sample_size": int(n), "categories": int(len(unique))}


def f1(tp: int, fp: int, fn: int) -> float:
    return 0.0 if 2 * tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn)


def matched_f1(reference: list[str], predicted: np.ndarray) -> dict[str, Any]:
    ref = np.asarray(reference, object)
    showers = sorted(set(reference) - {SPORADIC})
    clusters = sorted(int(x) for x in np.unique(predicted) if x >= 0)
    overlap = np.array([[np.sum((ref == s) & (predicted == c)) for c in clusters] for s in showers], dtype=int)
    assignment = {}
    if overlap.size:
        rr, cc = linear_sum_assignment(-overlap)
        assignment = {int(r): int(c) for r, c in zip(rr, cc)}
    per, values = {}, []
    for i, shower in enumerate(showers):
        true = ref == shower
        if i in assignment:
            cluster = clusters[assignment[i]]
            pred = predicted == cluster
            tp, fp, fn = int(np.sum(true & pred)), int(np.sum(~true & pred)), int(np.sum(true & ~pred))
        else:
            cluster, tp, fp, fn = None, 0, 0, int(np.sum(true))
        value = f1(tp, fp, fn)
        values.append(value)
        per[shower] = {"size": int(np.sum(true)), "cluster": cluster, "f1": value, "tp": tp, "fp": fp, "fn": fn}
    true_sp, pred_noise = ref == SPORADIC, predicted == -1
    sp = f1(int(np.sum(true_sp & pred_noise)), int(np.sum(~true_sp & pred_noise)), int(np.sum(true_sp & ~pred_noise)))
    return {
        "reference_showers": len(showers), "matched_showers": len(assignment),
        "f1_gt_0_5": int(sum(v > .5 for v in values)), "f1_gt_0_8": int(sum(v > .8 for v in values)),
        "macro_f1": float(np.mean(values)) if values else 0.0,
        "median_f1": float(np.median(values)) if values else 0.0,
        "sporadic_noise_f1": sp, "per_shower": per,
    }


def run(rows: list[dict[str, Any]], classification: str) -> tuple[dict[str, Any], np.ndarray]:
    x = features(rows)
    reference = [str(r["label"]) for r in rows]
    categories = [SPORADIC] + sorted(set(reference) - {SPORADIC})
    code = {label: i for i, label in enumerate(categories)}
    y_true = np.array([code[label] for label in reference], dtype=int)
    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE, min_samples=None, metric="euclidean",
        algorithm="boruvka_balltree", cluster_selection_method="eom",
        allow_single_cluster=False, prediction_data=False, gen_min_span_tree=False,
        core_dist_n_jobs=-1,
    )
    y = np.asarray(model.fit_predict(x), dtype=int)
    clusters = sorted(int(v) for v in np.unique(y) if v >= 0)
    result = {
        "classification": classification, "events": len(rows), "reference_showers": len(categories)-1,
        "clusters": len(clusters), "noise_fraction": float(np.mean(y == -1)),
        "nmi": float(normalized_mutual_info_score(y_true, y)),
        "ari": float(adjusted_rand_score(y_true, y)),
        "silhouette_including_noise": silhouette(x, y, True),
        "silhouette_excluding_noise": silhouette(x, y, False),
        "hungarian": matched_f1(reference, y),
        "cluster_sizes": {str(v): int(np.sum(y == v)) for v in sorted(np.unique(y))},
    }
    return result, y


def strata(h: dict[str, Any]) -> dict[str, Any]:
    bins = {"lt10": [], "10_24": [], "25_49": [], "50_99": [], "ge100": []}
    for row in h["per_shower"].values():
        n = row["size"]
        key = "lt10" if n < 10 else "10_24" if n < 25 else "25_49" if n < 50 else "50_99" if n < 100 else "ge100"
        bins[key].append(row["f1"])
    return {k: {"showers": len(v), "mean_f1": float(np.mean(v)) if v else None,
                "median_f1": float(np.median(v)) if v else None,
                "f1_gt_0_5": sum(x > .5 for x in v), "f1_gt_0_8": sum(x > .8 for x in v)} for k, v in bins.items()}


def markdown(result: dict[str, Any]) -> str:
    p, f = result["primary"], result["full"]
    def row(x: dict[str, Any]) -> str:
        h = x["hungarian"]
        return f"| {x['events']} | {x['reference_showers']} | {x['clusters']} | {x['noise_fraction']:.4f} | {x['nmi']:.4f} | {x['ari']:.4f} | {h['f1_gt_0_5']} | {h['f1_gt_0_8']} |"
    return "\n".join([
        "# SonotaCo 2025 HDBSCAN catalogue comparison", "", f"Verdict: **`{result['verdict']}`**", "",
        "Catalogue-scale literature transfer only; not an episode comparison or blind OrbitTrace rediscovery test.", "",
        "| Track | Events | Reference showers | HDBSCAN clusters | Noise | NMI | ARI | F1>.5 | F1>.8 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| Primary faithful transfer " + row(p)[1:], "| All-shower coverage audit " + row(f)[1:], "",
        f"Primary sporadic/noise F1: **{p['hungarian']['sporadic_noise_f1']:.4f}**; shower macro-F1: **{p['hungarian']['macro_f1']:.4f}**.", "",
        "The primary track uses the published unnormalized GEO vector, eom selection, minimum cluster size 100, the paper's quality filters, and only showers retaining at least 100 quality-filtered members. The all-shower run changes no HDBSCAN parameter and is reported only as a predeclared coverage diagnostic.", "",
    ])


def main() -> None:
    a = args(); a.output.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(a.protocol.read_text())
    base = module("hdb_catalogue_base", decode_file(a.baseline_payload), BASE_SHA)
    adapter = module("hdb_catalogue_adapter", decode_parts(a.adapter_parts), ADAPTER_SHA)
    labeled, sporadic, parser_audit = adapter.parse_sonotaco_events(a.archive, a.audit, base)
    side, side_audit = quality_sidecars(a.archive)
    all_rows = records(labeled, sporadic, side)
    quality = [r for r in all_rows if r["quality"]]
    counts = Counter(r["label"] for r in quality if r["label"] != SPORADIC)
    retained = sorted(label for label, count in counts.items() if count >= 100)
    primary_rows = [r for r in quality if r["label"] == SPORADIC or r["label"] in retained]
    if not quality or not primary_rows:
        raise RuntimeError("empty quality-filtered catalogue")
    primary, primary_y = run(primary_rows, "faithful reference-label-filtered transfer")
    full, full_y = run(quality, "predeclared all-shower coverage audit")
    gates = {
        "protocol_frozen": protocol.get("status") == "frozen_before_sonotaco_2025_execution",
        "development_corpus_exact": protocol.get("development_corpus") == "SonotaCo 2025 only",
        "archive_exact": side_audit["archive_sha256"] == ARCHIVE_SHA,
        "member_exact": side_audit["member_sha256"] == MEMBER_SHA,
        "parser_all_pass": all(parser_audit["gates"].values()),
        "sidecars_cover_parser_universe": len(all_rows) == len(labeled) + len(sporadic),
        "hdbscan_version": pkg_version("hdbscan") == HDBSCAN_VERSION,
        "sklearn_version": sklearn.__version__ == SKLEARN_VERSION,
        "feature_shapes": features(primary_rows).shape == (len(primary_rows), 6) and features(quality).shape == (len(quality), 6),
        "primary_labels_ge100_or_sporadic": all(r["label"] == SPORADIC or counts[r["label"]] >= 100 for r in primary_rows),
        "all_sporadics_retained_primary": sum(r["label"] == SPORADIC for r in primary_rows) == sum(r["label"] == SPORADIC for r in quality),
        "cluster_runs_complete": len(primary_y) == len(primary_rows) and len(full_y) == len(quality),
    }
    verdict = "PASS_SONOTACO_2025_HDBSCAN_CATALOGUE_TRANSFER" if all(gates.values()) else "FAIL_SONOTACO_2025_HDBSCAN_CATALOGUE_TRANSFER"
    result = {
        "verdict": verdict,
        "configuration": {"year": YEAR, "corpus": CORPUS, "feature": "unnormalized GEO", "min_cluster_size": 100,
                          "min_samples": None, "metric": "euclidean", "backend": "boruvka_balltree",
                          "selection": "eom", "hdbscan_version": pkg_version("hdbscan"), "sklearn_version": sklearn.__version__},
        "protocol_sha256": sha(a.protocol.read_bytes()), "parser_audit": parser_audit, "sidecar_audit": side_audit,
        "counts": {"parsed": len(all_rows), "quality": len(quality), "quality_sporadic": sum(r["label"] == SPORADIC for r in quality),
                   "quality_showers": len(counts), "primary_showers": len(retained), "primary_labels": retained,
                   "quality_shower_counts": dict(sorted(counts.items()))},
        "primary": primary, "full": full, "full_size_strata": strata(full["hungarian"]), "gates": gates,
        "boundaries": ["not episode-scale", "not blind OrbitTrace rediscovery", "no tuning on SonotaCo 2023"],
    }
    (a.output / "sonotaco_2025_hdbscan_catalogue.json").write_text(json.dumps(result, indent=2) + "\n")
    (a.output / "SONOTACO_2025_HDBSCAN_CATALOGUE.md").write_text(markdown(result))
    assignments = {"primary_ids": [r["id"] for r in primary_rows], "primary_labels": primary_y.tolist(),
                   "full_ids": [r["id"] for r in quality], "full_labels": full_y.tolist()}
    (a.output / "hdbscan_catalogue_assignments.json.gz").write_bytes(gzip.compress(json.dumps(assignments, separators=(",", ":")).encode()))
    print(markdown(result))
    if verdict.startswith("FAIL"):
        raise SystemExit(verdict)

if __name__ == "__main__":
    main()
