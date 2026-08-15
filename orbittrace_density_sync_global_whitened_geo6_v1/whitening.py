from __future__ import annotations

from dataclasses import dataclass

import numpy as np

METHOD_ID = "orbittrace_density_sync_global_whitened_geo6_v1"
DIM = 6
COV_TOL = 1e-10


@dataclass(frozen=True)
class WhiteningFit:
    mean: np.ndarray
    covariance: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    matrix: np.ndarray


def fit_whitener(x: np.ndarray) -> WhiteningFit:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != DIM or x.shape[0] <= DIM or not np.all(np.isfinite(x)):
        raise ValueError("invalid GEO6 matrix")
    mean = np.mean(x, axis=0)
    covariance = np.cov(x, rowvar=False, ddof=1)
    if covariance.shape != (DIM, DIM) or not np.all(np.isfinite(covariance)):
        raise ValueError("invalid covariance")
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if not np.all(np.isfinite(eigenvalues)) or np.any(eigenvalues <= 0.0):
        raise ValueError("covariance is not strictly positive definite")
    matrix = (eigenvectors * (eigenvalues ** -0.5)) @ eigenvectors.T
    if not np.all(np.isfinite(matrix)):
        raise ValueError("invalid whitening matrix")
    return WhiteningFit(mean, covariance, eigenvalues, eigenvectors, matrix)


def transform(x: np.ndarray, fit: WhiteningFit) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != DIM or not np.all(np.isfinite(x)):
        raise ValueError("invalid GEO6 matrix")
    z = (x - fit.mean) @ fit.matrix
    if not np.all(np.isfinite(z)):
        raise ValueError("non-finite whitened geometry")
    return z


def fit_transform(x: np.ndarray) -> tuple[np.ndarray, WhiteningFit, float]:
    fit = fit_whitener(x)
    z = transform(x, fit)
    cov_z = np.cov(z, rowvar=False, ddof=1)
    err = float(np.max(np.abs(cov_z - np.eye(DIM))))
    if not np.isfinite(err) or err > COV_TOL:
        raise ValueError(f"whitened covariance failed identity check: {err}")
    return z, fit, err
