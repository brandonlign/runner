"""Cross-fitted robust halo expansion for recurrent hierarchy candidates."""
from __future__ import annotations

from typing import Any

import numpy as np

from .config import V2Config


def _robust_center_scale(values: np.ndarray, floor: float) -> tuple[np.ndarray, np.ndarray]:
    center = np.median(values, axis=0)
    mad = np.median(np.abs(values - center[None, :]), axis=0) * 1.4826
    q25, q75 = np.percentile(values, [25.0, 75.0], axis=0)
    iqr_scale = (q75 - q25) / 1.349
    scale = np.maximum(np.maximum(mad, iqr_scale), float(floor))
    return center, scale


def _distances(values: np.ndarray, center: np.ndarray, scale: np.ndarray, uncertainties: np.ndarray | None) -> np.ndarray:
    if uncertainties is None:
        denominator = scale[None, :]
    else:
        denominator = np.sqrt(scale[None, :] ** 2 + np.asarray(uncertainties, dtype=float) ** 2)
    return np.sqrt(np.sum(((values - center[None, :]) / denominator) ** 2, axis=1))


def _bh_qvalues(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    if values.size == 0:
        return values.copy()
    order = np.argsort(values, kind="mergesort")
    ranked = values[order]
    adjusted = np.minimum.accumulate((ranked * values.size / np.arange(1, values.size + 1))[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.minimum(adjusted, 1.0)
    return result


def _membership_pvalues(core_scores: np.ndarray, scores: np.ndarray) -> np.ndarray:
    core = np.asarray(core_scores, dtype=float)
    query = np.asarray(scores, dtype=float)
    sorted_core = np.sort(core)
    less_than = np.searchsorted(sorted_core, query, side="left")
    greater_equal = len(core) - less_than
    return (1.0 + greater_equal.astype(float)) / (len(core) + 1.0)


def expand_candidate(candidate: dict[str, Any], matrix: np.ndarray, years: np.ndarray, event_ids: np.ndarray | None = None, config: V2Config | None = None, *, uncertainties: np.ndarray | None = None, retain_member_diagnostics: bool = True) -> dict[str, Any]:
    config = config or V2Config()
    values = np.asarray(matrix, dtype=float)
    year_values = np.asarray(years, dtype=np.int64)
    if values.ndim != 2 or values.shape[0] != len(year_values):
        raise ValueError("matrix and years must have the same row count")
    if uncertainties is not None:
        uncertainty_values = np.asarray(uncertainties, dtype=float)
        if uncertainty_values.shape != values.shape or np.any(uncertainty_values < 0):
            raise ValueError("uncertainties must be non-negative and match matrix shape")
    else:
        uncertainty_values = None
    members = np.asarray(candidate.get("members", ()), dtype=int)
    if members.ndim != 1 or np.any(members < 0) or np.any(members >= len(values)):
        raise ValueError("candidate members must be valid row indices")
    members = np.unique(members)
    if members.size < config.halo_min_training_members:
        raise ValueError("candidate has too few core members for cross-fitting")
    ids = np.asarray(event_ids, dtype=str) if event_ids is not None else None
    if ids is not None and ids.shape != (len(values),):
        raise ValueError("event_ids must align with matrix rows")
    expanded: set[int] = set(int(value) for value in members)
    iteration_folds: list[dict[str, dict[str, Any]]] = []
    for iteration in range(int(config.halo_iterations)):
        snapshot = np.asarray(sorted(expanded), dtype=int)
        additions: set[int] = set()
        folds: dict[str, dict[str, Any]] = {}
        for year in sorted(int(value) for value in np.unique(year_values)):
            heldout = np.flatnonzero(year_values == year)
            training = snapshot[year_values[snapshot] != year]
            if len(training) < config.halo_min_training_members or heldout.size == 0:
                folds[str(year)] = {"training_core": int(len(training)), "heldout_events": int(len(heldout)), "skipped": True, "reason": "insufficient_crossfit_training"}
                continue
            train_values = values[training]
            center, scale = _robust_center_scale(train_values, config.halo_scale_floor)
            train_uncertainties = None if uncertainty_values is None else uncertainty_values[training]
            core_scores = _distances(train_values, center, scale, train_uncertainties)
            cutoff = float(np.quantile(core_scores, 1.0 - config.halo_core_tail_alpha))
            heldout_uncertainties = None if uncertainty_values is None else uncertainty_values[heldout]
            scores = _distances(values[heldout], center, scale, heldout_uncertainties)
            conformity = _membership_pvalues(core_scores, scores)
            sorted_scores = np.sort(scores)
            background_counts = np.searchsorted(sorted_scores, scores, side="right")
            background_p = (1.0 + background_counts.astype(float)) / (len(scores) + 1.0)
            background_q = _bh_qvalues(background_p)
            accepted_mask = scores <= cutoff
            if config.halo_enforce_density_fdr:
                accepted_mask &= background_q <= config.halo_density_fdr
            accepted = heldout[accepted_mask]
            fold_additions = {int(value) for value in accepted if int(value) not in snapshot}
            additions.update(fold_additions)
            fold: dict[str, Any] = {
                "training_active_members": int(len(training)), "heldout_events": int(len(heldout)), "accepted_events": int(len(accepted)), "new_events": int(len(fold_additions)), "skipped": False,
                "center": center.tolist(), "scale": scale.tolist(), "core_cutoff": cutoff, "accepted_fraction": float(len(accepted) / len(heldout)),
                "max_accepted_background_q": float(np.max(background_q[accepted_mask])) if np.any(accepted_mask) else None,
                "mean_accepted_conformity": float(np.mean(conformity[accepted_mask])) if np.any(accepted_mask) else None,
                "density_fdr_enforced": bool(config.halo_enforce_density_fdr),
            }
            if retain_member_diagnostics:
                fold["accepted_indices"] = [int(value) for value in accepted.tolist()]
            if ids is not None and retain_member_diagnostics:
                fold["accepted_event_ids"] = [str(value) for value in ids[accepted].tolist()]
            folds[str(year)] = fold
        expanded.update(additions)
        iteration_folds.append(folds)
        if not additions:
            break
    expanded_indices = np.asarray(sorted(expanded), dtype=int)
    result = dict(candidate)
    result["core_members"] = [int(value) for value in members.tolist()]
    result["expanded_members"] = [int(value) for value in expanded_indices.tolist()]
    result["expanded_member_count"] = int(len(expanded_indices))
    result["halo_added_count"] = int(len(expanded_indices) - len(members))
    if ids is not None:
        result["expanded_event_ids"] = [str(value) for value in ids[expanded_indices].tolist()]
    result["crossfit_halo"] = {"iterations": iteration_folds, "folds": iteration_folds[-1] if iteration_folds else {}, "iterations_run": int(len(iteration_folds)), "core_tail_alpha": float(config.halo_core_tail_alpha), "scale_floor": float(config.halo_scale_floor), "density_fdr_enforced": bool(config.halo_enforce_density_fdr), "density_fdr": float(config.halo_density_fdr), "method": "leave-one-year-out robust diagonal conformal envelope"}
    return result


__all__ = ["expand_candidate"]
