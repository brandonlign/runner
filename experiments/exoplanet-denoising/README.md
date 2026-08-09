# Exoplanet denoising research runner

This directory is an isolated execution harness for the private `brandonlign/exoplanet-transit-denoising` research branch.

Isolation contract:

- The harness lives only on `agent/exoplanet-denoising-research-runner` unless explicitly promoted later.
- It does not modify `runner/main` or any OrbitTrace experiment paths.
- Its workflow is branch-scoped to `agent/exoplanet-denoising-research-runner` and path-scoped to this harness/workflow.
- The workflow has read-only permission to the public `runner` repository.
- Private source code/data are checked out only at runtime from `brandonlign/exoplanet-transit-denoising` branch `agent/research-upgrade-wavelength-preserving` when a suitable cross-repository token secret is available.
- Numerical outputs and captured logs are committed back only to that private research branch. They are not uploaded as public runner artifacts and are not printed into the public runner log.
- No workflow step pushes to `runner`, `runner/main`, or any OrbitTrace branch.

The first frozen research gates are:

1. Fair same-input Ridge/MLP baselines using the same rich signal + metadata information as the Hybrid.
2. A cross-fitted Ridge + DeepCNN residual experiment whose second-stage targets are generated out-of-fold.

The wavelength-preserving raw AIRS experiment remains in the private source branch because the raw parquet dataset is intentionally not copied into this public runner repository.
