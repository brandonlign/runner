# P2 execution-only D_SH batching freeze

This decision is frozen before any P2 scientific execution or result.

The exact scientific P2 source remains SHA-256 `7637b6fb310ee3f24f1de8479a34d10c594dc55471eee55b8854e1c28787e8dd`. The exact Southworth-Hawkins comparator remains SHA-256 `85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a`.

Only the candidate partition size used when calling that exact comparator changes from the frozen source default 512 to fixed 64 via `run_development_batch64.py`.

Source-only synthetic audits:

- workflow `31282922128`: batch 512, 8, and 31 produced bitwise-identical minimum D_SH outputs; batch 8 was 5.225x faster than 512 for 2,048 candidates / 8 source seeds;
- workflow `31282964683`: all tested batches 8, 16, 32, 64, 128 were bitwise-identical to 512 for 4,096 candidates and source-seed counts 4, 8, 16, 32, 64;
- fixed batch 64 synthetic speedup over 512 was approximately 6.86x, 6.01x, 5.14x, 3.98x, and 2.57x for source-seed counts 4, 8, 16, 32, and 64 respectively.

Fixed 64 is chosen as a simple robust execution rule rather than a data-dependent adaptive rule. It is not a scientific threshold and may not be changed from any P2 meteor-data result.

No meteor catalogue, shower-label value, excluded target-region event, or OrbitTrace target information entered either performance audit.
