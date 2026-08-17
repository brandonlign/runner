# Engineering notes

Run `32035051841` failed before candidate construction because the new workflow omitted the exact frozen `multi_anchor_energy_v3` / wavelet runtime plumbing used by the authoritative GMN TopoModal workflow.

Commit `3ae4bd5aa3f19bc3dd5455f4e4debe0c6b681959` restored only that frozen runtime setup. It did not alter `PROTOCOL.md`, `run_pretruth.py`, `evaluate_after_freeze.py`, the inherited Predictive Tree Cut selector, the TopoModal generator, the comparator, any parameter, any budget, or any scientific gate.

The subsequent run `32035358123` passed the runtime/source checks and reached the frozen pretruth structural gate, where it failed scientifically at `d=128, bucket=0, year=2022` because the selector produced `24 < K=29` candidates. The evaluation job remained skipped.
