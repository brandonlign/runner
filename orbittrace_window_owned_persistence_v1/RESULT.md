# OrbitTrace window-owned local persistence cross-scale diagnostic v1 — binding result

## 🟢 POSITIVE

Authoritative run: `31955534534`

Job: `95185494472`

Artifact: `orbittrace-window-owned-persistence-v1` (`9265879930`)

Artifact digest: `sha256:88ef704de42deb80fc82106a6cf86f0e3501ff870c729b62a9693bf188cb28e2`

Result SHA-256: `78a07a191e8705d2657c4c687d6db51b97d67cc9b4efb899f686c71dbe8f7bf8`

Execution head: `1bb5ab705c1f87277b90fd6e01fdce400e23b47a`

Interpretation: **`SUPPORTS_WINDOW_OWNED_PERSISTENCE_CROSS_SCALE_COHERENCE`**

The run used only target-excluded GMN 2022+2023 geometry and no shower truth. The exact GEO6 representation, 10°/5° windows, Persistable midpoint ladder, nearest-window ownership rule, nested thinning subsets, recurrent-EOM comparator, symmetric coherence metric, and all pass gates were frozen before the first valid outcome.

## Main structural comparison

Window-owned local persistence beat exact recurrent-EOM on every frozen aggregate comparison:

- pooled symmetric mean-best-Jaccard: **0.6952887378** vs **0.4574376105**;
- median bucket symmetric mean-best-Jaccard: **0.6959402473** vs **0.4786595472**;
- strict bucket wins: **4/4**;
- pooled fine→coarse mean-best-Jaccard: **0.6563369733** vs **0.6236539582**;
- pooled coarse→fine mean-best-Jaccard: **0.7342405024** vs **0.2912212628**.

Thus the improvement is not an artifact of generating more fine candidates: the reverse coarse→fine direction, which penalizes unmatched coarse candidates, improves dramatically as well.

## Bucket results

Symmetric mean-best-Jaccard (window-owned / recurrent-EOM):

- bucket 0: **0.6507753056 / 0.4499414024**;
- bucket 1: **0.6911088689 / 0.5110756349**;
- bucket 2: **0.7007716257 / 0.3749002034**;
- bucket 3: **0.7344864377 / 0.5073776920**.

Window-owned persistence won all four buckets.

## Candidate capacity

At the coarse ~5.8k scale, window-owned candidate counts were:

- `197 / 188 / 196 / 187`

versus recurrent-EOM:

- `28 / 32 / 37 / 33`.

At the fine ~0.7k scale, window-owned candidate counts were:

- **`111 / 112 / 106 / 118`**

versus recurrent-EOM:

- **`9 / 5 / 6 / 9`**.

Therefore the frozen fine-candidate non-collapse gate passed in all four buckets. This directly repairs the low-capacity failure of the global Persistable ladder, which emitted only `3/4/4/3` fine candidates.

The maximum number of pre-ownership ladder candidates in any one local window was only `7` at the coarse scale and `6` at the fine scale, far below the frozen per-window architectural ceiling of 119. Owned candidates were distributed across 65–66 active windows at the coarse scale and 52–57 active windows at the fine scale rather than percolating into a few global families.

## Membership stability details

Directional bucket scores remained strong. For example, bucket 2 achieved:

- fine→coarse **0.6810555333**;
- coarse→fine **0.7204877182**;
- symmetric **0.7007716257**;

versus recurrent-EOM symmetric **0.3749002034**.

Exact restricted membership matches were nonzero across all four window-owned buckets, with fine→coarse exact fractions approximately `0.117 / 0.170 / 0.208 / 0.178`.

## Interpretation and authorization boundary

This is the first post-ASFN structural architecture in the current repair sequence to satisfy **all** preregistered real-GMN cross-scale gates while also retaining substantially greater small-sample candidate capacity than recurrent-EOM.

The result supports the mechanism that independent local persistent hierarchies plus deterministic nearest-window ownership can avoid both:

1. the fixed-support/sample-size collapse of recurrent-EOM HDBSCAN; and
2. the cross-window/transitive percolation that damaged earlier catalogue-field constructions.

This result is **not yet a shower-recovery or literature-superiority result**. It uses no truth and provides no ranking. It authorizes only a separately frozen target-excluded GMN recovery/ranking successor built from the exact window-owned candidate architecture. No protected target, SonotaCo, ASFN/EFN event-level data, AMOS, MAARSY, or DMS access is authorized.

The exact structural architecture may not be silently altered from this result via window width/step, ownership rule, GEO6 representation, ladder range, support, Persistable neighbor policy, flattening, or cross-scale gate.