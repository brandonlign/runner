# TopoModal representative-share OOF v1 — Technical Repair 01 freeze

## Status

**FROZEN BEFORE REPAIR IMPLEMENTATION AND BEFORE ANY TECHNICALLY VALID SCIENTIFIC ENDPOINT.**

The first execution attempt of the frozen TopoModal representative-share OOF v1 endpoint was GitHub Actions run `32085559553`, head `481fd1505c7d8ba50e5db7a01ec8f6b4328ea05a`.

That run is a **technical no-result**, not a scientific PASS or FAIL.

All immutable source, runtime, and predecessor-pretruth checks passed. The endpoint opened only the already-authorized target-excluded GMN development truth and proceeded through target construction / OOF training to metric packaging, but no `TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1.json` result was written and the binding 12-gate contract was never evaluated.

## Exact failure

The frozen additional zero-filled-MRR adapter iterated the inherited `first_rank_by_label` map and executed `int(rank)` for every value. The inherited evaluator represents an eligible but unrecovered shower with `rank = None`.

Observed exception:

```text
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
```

at `metric_record(...)` before any scientific verdict.

## Authorized repair — interface/evaluation semantics only

The protocol already freezes zero-filled eligible-query MRR as:

- reciprocal rank `1/r` for an eligible shower recovered first at rank `r`;
- reciprocal rank `0` for an eligible shower not recovered;
- mean over all eligible showers.

Therefore the only authorized code change is to make the adapter implement that already-frozen definition correctly:

1. if a `first_rank_by_label` value is `None`, contribute `0` and do not cast it to integer;
2. `recovered_label_count` counts only non-`None` first-rank values;
3. retain the denominator `eligible_label_count` unchanged;
4. require every non-`None` rank to be an integer >= 1.

No other line of scientific logic may change.

## Explicitly unchanged

- protocol and all 12 promotion gates;
- exact sealed predecessor pretruth SHA-256 `22ee242d16e73c553d0e2041e55a8d938963c504a824797e92119d15b4bab7ba`;
- candidate memberships / hierarchy / event universes;
- group assignment;
- panelwise/yearwise representative-share target;
- whole-shower fold salt and fold assignments;
- 16-D feature map;
- ExtraTrees implementation, capacities, grouped weights, nested OOF;
- antichain recursion;
- candidate ordering and equal budgets;
- inherited historical conditional MRR;
- protected-data firewall and external-data access rules.

The first subsequent run that clears this exact technical defect and writes a complete result satisfying the frozen result schema is the first technically valid and binding scientific endpoint for this mechanism.