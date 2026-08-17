# OrbitTrace v31 quality × component full-universe selectivity diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after binding v41 failed and #1091 showed that the exact logical intersection

`joint_signal = (quality_suppression > 0) AND component_closure_opportunity`

is present in 5/9 versus 0/9 missed/surfaced recoverable HDB groups in 2013 and 4/9 versus 0/9 in 2014. #1091 conditions on annual-recoverable groups, so it cannot establish whether the same truth-free signal is sparse/selective enough across the complete fixed HDB candidate universe to support a candidate-level successor.

This diagnostic fills only that gap. It evaluates no new rank, score, selector, replacement rule, panel, cutoff, top-k, or successor.

## Frozen inputs and identities

Use only:

- immutable #950 Sugar/HDB pretruth payload and memberships;
- exact frozen #839 ranker source;
- exact v31 OOF reconstruction and controls inherited from frozen v40 source commit `31704c312c09be2765ad3f65a0685d1acfd2b055`;
- exact #1064 radius-1 Sugar↔HDB graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- exact #1072 connected-component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`;
- the immutable HDB `quality_order` already stored in the #950 pretruth manifest.

The graph/components must be reconstructed before exposed truth is loaded and match those exact SHA identities.

Exact v31 controls must reproduce after truth is loaded:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

No v31 scientific quantity is changed.

## Exact all-family joint signal

After exact v31 ranks are reconstructed, define for every one of the fixed 229 HDB families:

- `p_hdb = (v31_hdb_rank - 1) / 228`;
- `p_quality = (quality_rank - 1) / 228`;
- `positive_quality_suppression = p_hdb > p_quality`;
- `component_best_percentile = min((v31_route_rank-1)/(N_route-1))` over every Sugar/HDB member in that family's already-frozen #1072 component;
- `component_closure_opportunity = component_best_percentile < p_hdb`;
- `joint_signal = positive_quality_suppression AND component_closure_opportunity`.

This is exactly the candidate-level extension of #1091's two frozen binary directions. No suppression magnitude, component-size term, calibrated q, rank window, threshold, distance, overlap, route exception, or alternate Boolean rule is allowed.

## Truth-aware selectivity diagnostic

Only after the complete 229-family signal vector and its SHA-256 are fixed, use the immutable exposed SonotaCo truth to diagnose selectivity.

For every fixed HDB family, retain the unchanged v22 strict recurrent best-label definition. For each year, compute annual F1 for that unchanged label exactly as in v24. Define:

- `family_recoverable_y = annual_F1_y > 0.5`;
- strict diagnostic group = `SHOWER/<best_label>` for positive recurrent families, otherwise unique `NEG/<family_id>`;
- `group_joint_signal = any(joint_signal)` over fixed families in that diagnostic group;
- `group_recoverable_y = any(family_recoverable_y)` over the group.

Report for each year:

### Family level
- joint/nonjoint family counts;
- recoverable counts and fractions in each set;
- risk ratio `P(recoverable|joint) / P(recoverable|nonjoint)` when defined.

### Diagnostic-group level
- joint/nonjoint group counts;
- recoverable counts and fractions in each set;
- risk ratio `P(recoverable|joint) / P(recoverable|nonjoint)` when defined.

Also report the total joint-signal family fraction and group fraction as descriptive breadth measures only.

## Predeclared interpretation gate

The exact AND signal is considered full-universe selective only if **both years** satisfy all four strict inequalities:

1. family-level recoverable fraction among joint-signal families > the nonjoint recoverable fraction;
2. family-level joint risk ratio > 1;
3. diagnostic-group recoverable fraction among joint-signal groups > the nonjoint recoverable fraction;
4. diagnostic-group joint risk ratio > 1.

No minimum effect size, maximum signal-set size, p-value threshold, odds-ratio threshold, or precision cutoff is selected.

A PASS means only that the candidate-level AND direction survives a full-universe false-positive audit and may justify one separately frozen sparse-order architecture. It does **not** specify how signal-positive candidates should move, how many should move, or where they enter an order.

A FAIL closes categorical candidate-level use of this exact AND direction. No OR rule, magnitude threshold, top-k, rank window, component-size rule, or post-result alternate Boolean combination is authorized within this diagnostic.

## Explicit non-search commitments

No:

- new rank/score/selector/replacement/panel evaluation;
- suppression magnitude transform or threshold;
- component score/size/calibration rule;
- AND/OR/XOR/weight search;
- top-k, rank-window, budget/year-specific action;
- graph/component redefinition;
- feature/model/k/scaling/diversity/fusion/source-quota search;
- oracle identity hard-coding;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
