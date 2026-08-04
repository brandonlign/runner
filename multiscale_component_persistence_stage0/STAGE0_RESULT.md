# Multiscale component-persistence coherence: authoritative Stage-0 result

Runner workflow `30875976506` completed the frozen 2019/2021/2023/2025 development screen from source SHA-256 `66284b308fb0dc3356dc9c3d7df4b68816154556ba1b902773cca939ae0dd257`.

Artifact `8879615465` was preserved with digest `sha256:174d2e7ff9efc80bb89b44e8abf7025a4abf8d7bb7ecf2238a6c7f79e217f0c6`.

## Result

- component-persistence weak AUROC: **0.66038**;
- exact K4 / anchored quartet / LCC / density / DBSCAN: **0.76921 / 0.77016 / 0.77363 / 0.76978 / 0.74248**;
- pooled FPR at 0.05 / 0.01: **0.03841 / 0.00781**;
- worst year-sector FPR at 0.05: **0.10938**;
- k=4 recall at p <=0.05 / 0.01: **0.13864 / 0.04091**;
- k=6 / k=8 / k=12 recall at p <=0.05: **0.15758 / 0.14773 / 0.12234**;
- every complex fold AUROC was between **0.64278** and **0.67701**.

Only the three calibration gates passed. The candidate failed AUROC, every comparator and fold gate, k=4 sensitivity, k=6/k=8 preservation, and both monotonicity gates.

Verdict: **`KILL_MULTISCALE_COMPONENT_PERSISTENCE`**.

The isolation interval of a single-linkage component is not a useful sparse-stream signature in this background: genuine multi-member showers frequently merge into nearby structured background before forming a long-persistence isolated component. No component-size range, linkage rule, persistence transform, threshold, seed, or gate will be changed, and no confirmation-year or GhostStream application is authorized.
