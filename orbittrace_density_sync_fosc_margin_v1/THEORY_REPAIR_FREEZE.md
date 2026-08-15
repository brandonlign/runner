# Density-sync FOSC margin v1 — pre-GMN theory repair freeze

## Classification

**ENGINEERING / THEORY NO-RESULT BEFORE ANY SCIENTIFIC DATA ACCESS.**

The first zero-data synthetic audit exposed a false interpretation in the originally frozen protocol before any GMN catalogue, GMN scientific label, SonotaCo, AMOS, ASFN, EFN, MAARSY, DMS, OrbitTrace target information, or protected-region event was accessed by this successor.

Original frozen protocol blob: `e80458fcb6e12e40f0f78c3d03a09780f0709054`.
Original local-margin kernel blob: `786f13538f52fefcffca7f7a32b3e46e3a91efb5`.
Original synthetic audit blob: `5c97bb05071b88509e9d5384358f674c357c4c2f`.

Failed zero-data audit:

- run `31862832013`;
- job `94959037629`;
- artifact `9241107440`;
- artifact digest `sha256:67e071548652890c3dc7d6e239809f5dbafa23f3ba3c7c3d36ff050e5ae6f3c0`;
- execution head `34ccdff9324a1a1088fc0a09b543f2e7cb6a4b0c`.

The run reached only synthetic fixtures. It failed with:

`RuntimeError: global-loss theorem failed for node 15: 1.0 != 6.0`

No scientific endpoint or prelabel result exists from this audit.

## Exact theoretical error

The original protocol defined the local selected-node gap

`L(C) = S(C) - sum_{D in children(C)} O(D)`

and claimed it was the exact **global** FOSC objective loss if selected node `C` were forbidden.

That claim is false for a selected node lying below an unselected ancestor. If `C` is forbidden, an ancestor that was rejected in the unrestricted optimum can become preferable to its now-weakened descendant solution. The original local expression does not propagate that counterfactual upward.

Synthetic counterexample from the failed audit:

- node 12 has own objective `10`;
- its selected descendants 15 and 16 contribute `6 + 5 = 11`, so node 12 is rejected;
- local gap for selected leaf 15 is `6 - 0 = 6`;
- but when 15 is forbidden, node 12 can switch on with objective `10`, replacing the weakened descendant solution of `5`;
- the full optimum therefore falls only from `21` to `20`, an exact global loss of `1`, not `6`.

The local statistic itself is mathematically defined, but the stated global-counterfactual interpretation was wrong. It will **not** be silently relabeled and executed.

## Authorized pre-data repair

Because the error was detected on synthetic data before any scientific access, one theory-equivalent repair is authorized: replace the local gap with the exact forced-exclusion global FOSC loss.

For each final selected node `C`, define:

`G(C) = F* - F*_{-C}`

where:

- `F*` is the exact #1263 density-synchronous FOSC optimum with the HDBSCAN root excluded exactly as `allow_single_cluster=False`;
- `F*_{-C}` is the exact optimum under the sole constraint that node `C` itself may not be selected;
- every descendant and ancestor remains eligible under the original #1263 objective and tie semantics.

The forced optimum is computed deterministically by dynamic programming, not by tuning:

1. compute unrestricted subtree optima `O(N)=max(S(N), sum O(children(N)))` for all cluster nodes;
2. at forbidden node `C`, set the forced value to the descendant optimum `sum O(children(C))`;
3. propagate that changed child value upward along C's unique cluster-ancestor path; at each non-root ancestor `A`, recompute `max(S(A), forced_child_value + sum O(other children(A)))`;
4. at the excluded root, sum the forced value for the affected root-child branch plus the unchanged optima of the other root-child branches;
5. subtract from the unrestricted root-excluded optimum.

This exactly permits previously unselected ancestors to switch on under the counterfactual.

The scientific architecture remains ranking-only: exact #1263 hierarchy, density-synchronous objective, selected nodes, memberships and candidate universe are unchanged. No parameter, threshold, blend, normalization, feature, FOSC top-M value, external information or scientific result enters this repair.

The repaired theory and source must be frozen and must pass a new zero-data brute-force synthetic audit before any GMN workflow may be registered or activated.

If the repaired synthetic theorem audit fails, this successor remains ineligible for GMN until the purely mathematical inconsistency is resolved or the lane is abandoned. No scientific-data trial is authorized by this note.
