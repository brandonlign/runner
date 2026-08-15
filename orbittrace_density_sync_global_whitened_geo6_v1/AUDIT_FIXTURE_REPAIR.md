# Zero-truth audit fixture repair

Workflow run `31898232438` is a pre-data engineering no-result. The zero-truth whitening audit stopped the workflow before any GMN runtime artifact was downloaded and before any scientific catalogue access.

All substantive whitening checks passed: covariance identity error was `2.55351295663786e-15`, affine axis-rescaling distance error was `1.7763568394002505e-14`, the transform was deterministic/non-identity, eigenvalues were positive, and the whitened mean was numerically zero.

The sole failed audit assertion was `singular_covariance_fails_closed`. The synthetic fixture constructed its sixth column as a floating-point linear combination of two other random columns. Although mathematically rank-deficient, numerical covariance/eigendecomposition can return a tiny positive final eigenvalue, which correctly satisfies the frozen implementation's literal requirement that computed eigenvalues be strictly positive.

The audit-only repair replaces that fixture with a sixth coordinate that is exactly constant, whose sample covariance has an exact zero row/column and therefore tests the intended fail-closed branch without relying on numerical rank detection.

No whitening formula, covariance estimator, eigenvalue rule, tolerance, HDBSCAN setting, density-synchronous objective, promotion gate, dataset, or firewall rule changes. The first scientifically valid GMN execution remains unconsumed.