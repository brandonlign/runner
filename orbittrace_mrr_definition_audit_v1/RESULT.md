# OrbitTrace MRR definition audit v1 — binding result

## CONFIRMED — CURRENT CONDITIONAL MRR GATE IS NON-MONOTONE IN RECOVERY

Authoritative run: `32071605222`

Execution commit: `7917e10b361cdfb8633febc39c2c9dc9e2d0ed1f`

Artifact: `9301912731`

Artifact digest: `sha256:1e2d285face8c8d1e9300b4ad1dd6dace5f3630761d1f6bdb697c5581004144f`

Audit result SHA-256: `60da3799d1a843d8bb6adaff99d81ca01e3857201af29c4d6a9f779eaaf5a4a1`

Exact verdict:

`AUDIT_MRR_DEFINITION_PROBLEM_CONFIRMED`

This audit opened no new shower truth, generated no candidates, and reran no scientific successor. It used only the frozen Recurrent-EOM evaluator source and the already-sealed closed support-mask truth result.

## Source finding

The frozen evaluator computes MRR only across eligible showers with a finite recovered first rank. Eligible-but-unrecovered showers are excluded from the MRR denominator.

If the current conditional mean is `C=S/n` and a previously missed eligible shower is newly recovered at reciprocal rank `x=1/r`, then

`C' - C = (x - C)/(n+1)`.

Therefore a real new recovery **lowers** current MRR whenever `1/r < C`, even if every previously recovered shower retains exactly the same first rank.

With zero-filled eligible-query MRR `Z=S/E`, the same new recovery changes the metric by

`Z' - Z = x/E > 0`,

so a new finite-rank recovery cannot mechanically make the joint coverage/ranking metric worse when existing first ranks are unchanged.

## Fixed sealed example — recurrent-TopoModal support mask v1

### Fine sparse scale (`d=1024`)

- qualified recovery: `20 -> 28`
- current conditional MRR panel mean: `0.6959325397 -> 0.5641617063` (**lower**)
- zero-filled eligible-query MRR panel mean: `0.3308496315 -> 0.3916631236` (**higher**)
- pooled zero-filled reciprocal mass / eligible query: `0.2873376623 -> 0.3505952381` (**higher**)

### Coarse sparse scale (`d=128`)

- qualified recovery: `94 -> 119`
- current conditional MRR panel mean: `0.2358453098 -> 0.2063089116` (**lower**)
- zero-filled eligible-query MRR panel mean: `0.0644092270 -> 0.0723243266` (**higher**)
- pooled zero-filled reciprocal mass / eligible query: `0.0632519005 -> 0.0709633991` (**higher**)

All ten machine-checkable audit gates passed.

## Binding interpretation

This does **not** retroactively change any prior scientific verdict. Every previously closed successor remains closed under the protocol that governed its run.

For future candidate-rich OrbitTrace successors, however, conditional MRR should not automatically be reused as a mandatory non-regression gate when recovery counts differ. A future protocol may instead pre-freeze zero-filled eligible-query MRR or another independently justified joint retrieval/ranking metric before any new method outcome.

No protected target-region access is authorized by this audit. No champion changes here.
