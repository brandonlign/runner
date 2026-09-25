"""Frozen configuration for the Unified v3 development lane."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class V3Config:
    min_cluster_size: int = 8
    min_samples: int = 4
    core_dist_n_jobs: int = 1
    hierarchy_max_rows_per_year: int = 30000
    hierarchy_sample_seed: int = 20260822
    hierarchy_window_width_deg: float = 10.0
    hierarchy_window_stride_deg: float = 5.0
    hierarchy_dedup_jaccard: float = 0.80
    hierarchy_max_candidate_members: int = 300
    global_anchor_count: int = 32
    recurrence_quantile: float = 0.25
    min_year_support_fraction: float = 0.60
    min_year_events: int = 1
    feature_scales: tuple[float, float, float, float] = (3.5, 3.0, 2.5, 2.5)
    calibration_permutations: int = 9999
    calibration_seed: int = 20260822
    calibration_correction: str = "benjamini_yekutieli"
    halo_core_tail_alpha: float = 0.01
    halo_cutoff_inflation: float = 1.02
    halo_iterations: int = 2
    halo_orbit_distance_max: float = 0.15
    halo_scale_floor: float = 0.05
    halo_min_training_members: int = 8
    halo_enforce_density_fdr: bool = False
    halo_density_fdr: float = 0.10
    halo_background_shifts: int = 7
    def __post_init__(self) -> None:
        if self.min_cluster_size < 2 or self.min_samples < 1: raise ValueError("cluster sizes must be positive")
        if self.core_dist_n_jobs == 0: raise ValueError("core_dist_n_jobs cannot be zero")
        if self.hierarchy_max_rows_per_year < self.min_cluster_size: raise ValueError("hierarchy_max_rows_per_year must fit at least one cluster")
        if not 0.0 < self.hierarchy_window_width_deg <= 360.0: raise ValueError("hierarchy_window_width_deg must lie in (0, 360]")
        if not 0.0 < self.hierarchy_window_stride_deg <= self.hierarchy_window_width_deg: raise ValueError("hierarchy_window_stride_deg must lie in (0, width]")
        if not 0.0 < self.hierarchy_dedup_jaccard <= 1.0: raise ValueError("hierarchy_dedup_jaccard must lie in (0, 1]")
        if self.hierarchy_max_candidate_members < self.min_cluster_size: raise ValueError("hierarchy_max_candidate_members is too small")
        if self.global_anchor_count < 1: raise ValueError("global_anchor_count must be positive")
        if not 0.0 <= self.recurrence_quantile <= 1.0: raise ValueError("recurrence_quantile must lie in [0, 1]")
        if not 0.0 < self.min_year_support_fraction <= 1.0: raise ValueError("min_year_support_fraction must lie in (0, 1]")
        if self.min_year_events < 1: raise ValueError("min_year_events must be positive")
        if len(self.feature_scales) != 4 or any(value <= 0 for value in self.feature_scales): raise ValueError("feature_scales must contain four positive values")
        if self.calibration_permutations < 99: raise ValueError("calibration_permutations must be at least 99")
        if self.calibration_correction != "benjamini_yekutieli": raise ValueError("v3 freezes the dependence-safe BY correction")
        if not 0.0 < self.halo_core_tail_alpha < 1.0: raise ValueError("halo_core_tail_alpha must lie in (0, 1)")
        if self.halo_cutoff_inflation < 1.0: raise ValueError("halo_cutoff_inflation must be at least one")
        if self.halo_iterations < 1: raise ValueError("halo_iterations must be positive")
        if self.halo_orbit_distance_max <= 0.0 or self.halo_scale_floor <= 0.0: raise ValueError("halo distance and scale constants must be positive")
        if self.halo_min_training_members < 2: raise ValueError("halo_min_training_members must be at least two")
        if not 0.0 < self.halo_density_fdr < 1.0: raise ValueError("halo_density_fdr must lie in (0, 1)")
        if self.halo_background_shifts < 3: raise ValueError("halo_background_shifts must be at least three")
