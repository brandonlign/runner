# RFT v3 owned-only UV-parallel engineering fallback freeze

## Role

This is an **engineering-only fallback** frozen while the original RFT v3 GMN2023 heldout matrix run `31562188321` is still in progress and before any v3 heldout outcome is known. It does not change the scientific method, candidate universe, ranking rule, thresholds, heldout gates, or any label-dependent operation.

The active heldout workflow remains authoritative unless it fails for a technical execution reason. This fallback must never be invoked to alter or retry a scientifically valid GMN2023 outcome.

## Exact projection

Frozen original UV-parallel builder blob: `a94343f87c6021eb7da03dcf095378272fea97d3`.

Owned-only fallback builder blob: `20050ff3bf727af21e8c45fa21b76f58c445d57d`.

The original builder executes, in order:

1. exact deterministic perturbation;
2. the same fail-closed UV/parallel atom-equivalence probe;
3. the same UV-parallel atom construction;
4. `mod.build_tubes(atom_list, ownership=True)` to produce `owned`;
5. `mod.build_tubes(atom_list, ownership=False)` to produce `unowned`;
6. pack both outputs.

The fallback is the exact prefix through step 4 and packs only `owned`. It removes only step 5, whose output is scientifically unused by frozen RFT v3.

Frozen RFT v1 `build_tubes` blob is part of source blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`. The function constructs local dictionaries/lists/Tubes and returns a newly sorted list; it does not mutate the input atom objects/list. The original owned call occurs before the unowned call. Therefore deleting the later unowned call cannot change the already-created owned tube list.

## Permitted use

This fallback is permitted only if the original heldout execution suffers a technical failure such as runner shutdown/timeout before producing a scientifically valid aggregate. Any use must retain:

- exact RFT v3 protocol blob `1c296867271a23c076a221b4e45f539eb825b945`;
- exact v3 replica pre-access authorizer semantics;
- exact v1 geometry/atom sources and all current engineering source pins;
- exact owned tube bytes/order;
- exact v2 soft-evidence helper and `RFT2OWNED` namespace;
- exact five frozen GMN2023 heldout gates;
- no GMN2023 ablations, parameter search, reranking, or candidate changes.

If the original run yields a technically valid PASS / USEFUL_BUT_INSUFFICIENT / FAIL result, that result is binding and this fallback is not used.
