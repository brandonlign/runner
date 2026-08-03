from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
METHOD_ROOT = ROOT / "invariant_streamnet_stage0"
RESULTS = Path(__file__).resolve().parent / "results"
EXPECTED_SOURCE_SHA256 = "9e5aff4130b416c3b12d8b05bc88c8591adfd0b968bb454f6ffcfd7ef81e56e7"
SEED = 20260804


def load_source_module():
    encoded = "".join((METHOD_ROOT / "run_stage0.py.gz.b64").read_text(encoding="ascii").split())
    source = gzip.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"Source SHA mismatch: {digest}")
    extracted = Path("/tmp/invariant_streamnet_frozen_source.py")
    extracted.write_bytes(source)
    spec = importlib.util.spec_from_file_location("invariant_streamnet_frozen", extracted)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import frozen source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def f1_at_threshold(probabilities: np.ndarray, truth: np.ndarray, threshold: float) -> dict[str, float]:
    pred = probabilities >= threshold
    actual = truth.astype(bool)
    tp = float(np.sum(pred & actual))
    fp = float(np.sum(pred & ~actual))
    fn = float(np.sum(~pred & actual))
    precision = tp / max(tp + fp, 1.0)
    recall = tp / max(tp + fn, 1.0)
    f1 = 2.0 * precision * recall / max(precision + recall, 1e-12)
    return {
        "threshold": float(threshold),
        "predicted_members": int(np.sum(pred)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def probability_summary(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "p05": float(np.quantile(values, 0.05)),
        "p25": float(np.quantile(values, 0.25)),
        "median": float(np.median(values)),
        "p75": float(np.quantile(values, 0.75)),
        "p95": float(np.quantile(values, 0.95)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    module = load_source_module()
    module.set_deterministic(module.SEED)
    rng = np.random.default_rng(SEED)

    model = module.InvariantStreamNet()
    state_path = METHOD_ROOT / "results/model_state.pt"
    model.load_state_dict(torch.load(state_path, map_location="cpu", weights_only=True))
    model.eval()

    stage0 = json.loads((METHOD_ROOT / "results/stage0_result.json").read_text(encoding="utf-8"))
    member_threshold = float(stage0["calibration_thresholds"]["membership"])

    data_root = Path("invariant_streamnet_diagnostic/data")
    values, provenance = module.download_and_load("GMN", data_root)
    full = module.NetworkIndex.build("GMN", values, remove_esv=False)
    background = module.NetworkIndex.build("GMN", values, remove_esv=True)

    def evaluate(index, center: np.ndarray) -> dict[str, object]:
        patch, original_indices = index.patch_at_center(center)
        logits, member_logits = module.predict_logits(model, patch[None, ...])
        probabilities = expit(member_logits[0])
        truth = module.esv_mask(values[original_indices]) if index is full else np.zeros(len(patch), dtype=bool)
        return {
            "center": center.tolist(),
            "raw_global_logit": float(logits[0]),
            "member_probability": probabilities,
            "truth": truth,
            "patch": patch,
            "original_indices": original_indices,
        }

    original = evaluate(full, module.ESV_CENTER.copy())

    offsets = list(
        itertools.product(
            (-3.0, 0.0, 3.0),
            (-4.0, 0.0, 4.0),
            (-2.0, 0.0, 2.0),
            (-1.5, 0.0, 1.5),
        )
    )
    esv_scan: list[dict[str, object]] = []
    for offset in offsets:
        center = module.ESV_CENTER + np.asarray(offset, dtype=np.float64)
        center[0] %= 360.0
        center[1] %= 360.0
        try:
            esv_scan.append(evaluate(full, center))
        except RuntimeError:
            continue
    best = max(esv_scan, key=lambda item: float(item["raw_global_logit"]))

    null_scan_maxima: list[float] = []
    null_center_count = 0
    shuffled = rng.permutation(background.allowed_indices)
    for center_index in shuffled:
        if null_center_count >= 120:
            break
        base = values[int(center_index)].copy()
        scores: list[float] = []
        for offset in offsets:
            center = base + np.asarray(offset, dtype=np.float64)
            center[0] %= 360.0
            center[1] %= 360.0
            try:
                evaluated = evaluate(background, center)
            except RuntimeError:
                continue
            scores.append(float(evaluated["raw_global_logit"]))
        if scores:
            null_scan_maxima.append(max(scores))
            null_center_count += 1

    synthetic_dense: dict[str, object] = {}
    for morphology in ("train", "unseen"):
        logits_all: list[float] = []
        probabilities_all: list[np.ndarray] = []
        truths_all: list[np.ndarray] = []
        for _ in range(160):
            patch, _ = background.sample_patch(rng)
            patch, truth = module.inject_stream(rng, patch, module.N_EVENTS, morphology)
            logits, member_logits = module.predict_logits(model, patch[None, ...])
            logits_all.append(float(logits[0]))
            probabilities_all.append(expit(member_logits[0]))
            truths_all.append(truth)
        probabilities = np.stack(probabilities_all)
        truth = np.stack(truths_all)
        metrics = f1_at_threshold(probabilities.reshape(-1), truth.reshape(-1), member_threshold)
        synthetic_dense[morphology] = {
            "patches": len(logits_all),
            "raw_global_logit_mean": float(np.mean(logits_all)),
            "raw_global_logit_p05": float(np.quantile(logits_all, 0.05)),
            "membership": metrics,
            "member_probability": probability_summary(probabilities.reshape(-1)),
        }

    thresholds = np.linspace(0.05, 0.90, 18)
    original_sweep = [f1_at_threshold(original["member_probability"], original["truth"], value) for value in thresholds]
    best_sweep = [f1_at_threshold(best["member_probability"], best["truth"], value) for value in thresholds]

    best_logit = float(best["raw_global_logit"])
    null_array = np.asarray(null_scan_maxima, dtype=np.float64)
    result = {
        "purpose": "post-hoc frozen-model diagnostic; not a continuation-gate rerun",
        "frozen_source_sha256": EXPECTED_SOURCE_SHA256,
        "model_state_sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
        "gmn_provenance": provenance,
        "member_threshold": member_threshold,
        "original_center": {
            "center": original["center"],
            "raw_global_logit": original["raw_global_logit"],
            "conservative_members": int(np.sum(original["truth"])),
            "member_probability": probability_summary(original["member_probability"]),
            "frozen_threshold_metrics": f1_at_threshold(original["member_probability"], original["truth"], member_threshold),
            "threshold_sweep": original_sweep,
            "local_coordinate_summary": {
                "mean": np.mean(original["patch"], axis=0).tolist(),
                "std": np.std(original["patch"], axis=0).tolist(),
                "min": np.min(original["patch"], axis=0).tolist(),
                "max": np.max(original["patch"], axis=0).tolist(),
            },
        },
        "center_scan": {
            "offset_count": len(offsets),
            "valid_esv_centers": len(esv_scan),
            "best_center": best["center"],
            "best_raw_global_logit": best_logit,
            "best_conservative_members": int(np.sum(best["truth"])),
            "best_member_probability": probability_summary(best["member_probability"]),
            "best_frozen_threshold_metrics": f1_at_threshold(best["member_probability"], best["truth"], member_threshold),
            "best_threshold_sweep": best_sweep,
            "null_scanned_centers": len(null_scan_maxima),
            "null_maximum_summary": probability_summary(null_array),
            "look_elsewhere_corrected_percentile": float(np.mean(null_array < best_logit)),
        },
        "synthetic_dense_control": synthetic_dense,
    }
    (RESULTS / "diagnostic.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    original_best_threshold = max(original_sweep, key=lambda item: float(item["f1"]))
    scan_best_threshold = max(best_sweep, key=lambda item: float(item["f1"]))
    report = [
        "# InvariantStreamNet frozen-model diagnostic",
        "",
        "This is a post-hoc diagnosis of the failed real-ESV transfer gates. It does not alter, rerun, or override the frozen Stage-0 verdict.",
        "",
        "## Original published center",
        "",
        f"- Raw global logit: {float(original['raw_global_logit']):.4f}",
        f"- Frozen membership threshold: {member_threshold:.2f}",
        f"- Member-probability median / maximum: {float(np.median(original['member_probability'])):.4f} / {float(np.max(original['member_probability'])):.4f}",
        f"- Predicted members at frozen threshold: {f1_at_threshold(original['member_probability'], original['truth'], member_threshold)['predicted_members']}",
        f"- Best post-hoc threshold F1: {float(original_best_threshold['f1']):.3f} at {float(original_best_threshold['threshold']):.2f}",
        "",
        "## Fair center scan",
        "",
        f"- Best center: {best['center']}",
        f"- Best raw logit: {best_logit:.4f}",
        f"- Percentile against null catalogs scanned over the identical offset bank: {float(np.mean(null_array < best_logit)):.4f}",
        f"- Predicted members at frozen threshold: {f1_at_threshold(best['member_probability'], best['truth'], member_threshold)['predicted_members']}",
        f"- Best post-hoc threshold F1: {float(scan_best_threshold['f1']):.3f} at {float(scan_best_threshold['threshold']):.2f}",
        "",
        "## Dense synthetic controls",
        "",
    ]
    for morphology, payload in synthetic_dense.items():
        report.append(
            f"- {morphology}: member F1 {payload['membership']['f1']:.3f}, predicted members {payload['membership']['predicted_members'] / payload['patches']:.1f} per 48"
        )
    report.extend(
        [
            "",
            "## Decision use",
            "",
            "If the fair scan remains non-significant and membership probabilities remain far below the frozen threshold while dense synthetic controls succeed, the failure is synthetic-to-real morphology transfer rather than center choice or stream occupancy. The current model must remain rejected.",
        ]
    )
    (RESULTS / "DIAGNOSTIC_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "original_raw_logit": original["raw_global_logit"],
        "original_member_summary": probability_summary(original["member_probability"]),
        "best_scan_logit": best_logit,
        "scan_percentile": float(np.mean(null_array < best_logit)),
        "best_center": best["center"],
        "best_frozen_members": f1_at_threshold(best["member_probability"], best["truth"], member_threshold)["predicted_members"],
        "synthetic_dense": synthetic_dense,
    }, indent=2))


if __name__ == "__main__":
    main()
