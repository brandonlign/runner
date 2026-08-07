# OrbitTrace v3-primary dual-output catalogue — v6 development

## Purpose

v6 is a new catalogue-stage architecture built after the failure of v4/v5 as universal merged binary episode decisions. It promotes the one result that transferred consistently across years: frozen **v3 multi-anchor wavelet energy** as the primary continuous episode ranker, while keeping frozen **fixed4** as a completely separate sparse rescue queue.

v6 is not a claim about historical OrbitTrace discovery. It is a target-free catalogue development test on 2022–2023 only.

## Frozen ancestry

Primary ranker:

- method: `orbittrace_multi_anchor_wavelet_energy_v3`;
- exact Brown-family 4° / 10%-speed geometry;
- top-four positive leave-one-out coefficient L2 energy;
- unchanged source from the frozen v3 development/transfer chain.

Cross-year episode evidence already observed before v6 catalogue development:

- 2025: v3 AUROC `0.836860 > 0.828506` Brown-family;
- 2023: v3 AUROC `0.836263 > 0.831972` Brown-family;
- 2020: v3 AUROC `0.802819 > 0.796782` Brown-family.

Sparse rescue:

- frozen fixed4 score and Mondrian empirical p-value;
- rescue cutoff `p_fixed4 <= 1/129`;
- never inserted into the v3 primary component graph, recurrence graph, Fisher evidence, or ranking.

Frozen catalogue infrastructure:

- exact base source SHA-256 `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`;
- development years 2022 and 2023 only;
- 10° windows stepped every 5°;
- 128-event local episodes;
- 128 null calibration episodes per 10° solar-longitude bin;
- positive-lobe membership radius `r² < 3`;
- component minimum four events and two retained anchors;
- cross-year centroid link radius `1.5`;
- solar longitude **20°–55° removed before label normalization/storage/candidate generation**;
- no 2024–2026 catalogue or OrbitTrace target information may be loaded.

## Why a bounded proposal stage is required

The older catalogue implementation generated roughly 256k provisional anchors in 2022 and 357k in 2023, then attempted exact rescoring of nearly all of them. That is unnecessary for v3 and computationally prohibitive because every exact v3 episode evaluates a 128×128 coefficient geometry.

Brown-family anchor coefficients therefore become **proposal-only computational screening information**. They are not final v6 scientific evidence.

The proposal budget is derived from the already frozen downstream capacity rather than fitted from labels:

- old post-exact anchor capacity: `36 bins × (128 components/bin × 8 anchors/component) = 36,864 anchors/year`;
- v6 primary proposal capacity: `72 windows × 512 proposals/window = 36,864 proposals/year`;
- therefore `512 = MAX_COMPONENTS_PER_BIN × 4` is fixed before development.

For each supported 10° window:

1. use the unchanged 32-neighbor positive-lobe prefilter and 256-neighbor shortlist;
2. compute the unchanged proposal-anchor Brown coefficient and fixed4 score;
3. rank all eligible proposal anchors by `(Brown empirical p, -Brown score, fixed4 p, anchor id)`;
4. retain the top 512 primary proposals;
5. additionally retain every fixed4 minimum-p proposal (`p_fixed4 <= 1/129`), even if outside the 512 primary budget;
6. deduplicate overlapping-window proposal anchors deterministically before expensive exact v3 rescoring.

No known-shower label enters this proposal stage.

## Exact v3 rescoring

Each retained proposal anchor is rebuilt from the complete 10° window using the exact 127 nearest Brown-geometry neighbors plus the proposal anchor.

On that exact 128-event episode:

- compute frozen v3 multi-anchor energy;
- compute an empirical v3 p-value from the same bin's 128 null episodes;
- compute fixed4 p-value independently;
- compute the exact Brown proposal-anchor coefficient only as a diagnostic/proposal provenance field.

For a v3 detection, the strongest positive v3 coefficient location becomes the representative anchor. Its `r² < 3` positive-lobe neighborhood defines the primary member set. This ties catalogue membership to the event location actually producing the v3 evidence rather than to the earlier computational proposal anchor.

For a fixed4-only rescue detection, the proposal-anchor positive-lobe membership is retained for the rescue queue.

Primary detection cutoff remains `p_v3 <= 0.05`. Sparse rescue remains `p_fixed4 <= 1/129`.

## Strict dual-output separation

Primary v3 anchors and fixed4 rescue anchors are never mixed when building connected components.

- v3 anchors -> v3 components -> v3 recurrent families -> v3 ranking;
- fixed4 rescue anchors -> rescue components -> rescue recurrent families -> separate rescue queue.

A fixed4 rescue cannot increase a v3 family's event count, component count, year recurrence, Fisher evidence, or rank. An anchor that satisfies both channels may appear independently in both outputs, but the graphs remain separate.

## Primary family ranking

For v3 components linked across 2022 and 2023, rank by:

1. larger year count;
2. larger Fisher-style evidence `sum(-log(best v3 empirical p per year))`;
3. larger best v3 score;
4. larger event support.

The fixed4 rescue queue is separately ranked by recurrence, fixed4 empirical evidence, and support. It is never interleaved with the primary v3 list.

## Development evaluation and gates

Labels remain hidden until after candidate generation, exact scoring, component construction, recurrence linking, and ranking are complete.

Use the same eligible known-shower definition as the frozen catalogue benchmark: at least eight total labelled events and at least four in each development year.

The frozen fixed4 persistence baseline is workflow `31106001133`, artifact `8971289223`, artifact SHA-256 `01a7158ee5cf79e212689b3eb24438bbf98f959dc3588141f073412b1a9c5999`, with:

- top-100 recovered labels `61`;
- qualified matches `90`;
- top-100 dominant precision `0.6809376504699393`.

v6 passes development only if every gate holds:

- frozen v3 self-tests and v3-membership equivalence tests pass;
- exact base catalogue source hash matches;
- target exclusion and development years remain exact;
- at least 30 supported calibration bins in each year;
- proposal budget is exactly 512/window and 36,864 primary proposals/year maximum;
- at least 50 recurrent **v3 primary** families;
- v3 top-100 known-shower recovery >= `floor(0.8 × 61) = 48`;
- v3 top-100 dominant precision >= `0.50`;
- v3 qualified known-shower matches >= `floor(0.6 × 90) = 54`.

Rescue-only additions are reported but do not help the primary gates.

A scientific failure is frozen and does not authorize same-result tuning. A technical failure before a scientific result may be repaired without changing this protocol.

## Claim boundary

A v6 development pass would establish that the frozen v3 episode ranker can drive a target-free recurrent catalogue pipeline on the 2022–2023 development panel while fixed4 remains a separate sparse channel. It would not establish historical discovery, blind OrbitTrace recovery, or target validation. Those require later frozen stages with the target interval still excluded until the appropriate reveal.
