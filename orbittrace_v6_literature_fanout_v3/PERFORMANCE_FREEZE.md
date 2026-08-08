# Matched-literature fanout v3 performance freeze

Infrastructure-only acceleration prepared before any v6 matched-literature result exists. It changes no detector, comparator, exact-row universe, truth mapping, threshold, score, membership, recurrence, ranking, or superiority criterion.

For each already-frozen HDBSCAN/Sugar × 2023/2025 panel-year:

1. materialize the exact ID-only pretruth geometry/background universe used by the existing matched-literature harness;
2. run the immutable v6 proposal/calibration path while replacing exact rescoring only with capture of its deduplicated center records and exact window-event IDs;
3. estimate exact geometry work as `record_count × window_event_count`;
4. split only oversized centers into contiguous proposal-record slices and schedule those slices deterministically by longest-processing-time across a fixed shard count;
5. every slice calls the same immutable `exact_rescore_window_v6` implementation, using the already-proven order-preserving 4-worker contiguous multiprocessing wrapper internally;
6. SHA-check complete nonoverlapping coverage of every center's proposal list, reconstruct exact outputs in original proposal order, and replay through immutable `scan_year_v6`;
7. emit the exact same pretruth checkpoint schema consumed by the frozen combine/evaluate literature harness;
8. open known-shower truth and comparator assignments only after all P1-independent v6 family rankings are frozen, exactly as in the existing adjudication.

Before scientific use this performance path requires source audit plus bounded exact-equivalence to the already-audited literature `run_pretruth_year.py` output. Failure rejects the accelerator, not the detector.

Solar longitude 20°–55° remains excluded throughout. No OrbitTrace target information enters this branch.
