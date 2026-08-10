# OrbitTrace v15 SonotaCo 2013/2014 engineering applicability v1

## Purpose

Test exactly one question after the canonical-format and label-free-v8/v15 deployment qualification chain:

**Can the same frozen survey-independent detector complete on the already-exposed SonotaCo 2013/2014 label-free base rows without the old fixed-128 local-episode crash?**

This is engineering applicability only. SonotaCo 2013/2014 was already scientifically exposed by the frozen #839 final attempt, so this run cannot restore pristine external-validation status and must not evaluate known-shower truth, Sugar, HDBSCAN, #854, or any literature-superiority metric.

The run is dormant unless the immediately preceding GMN qualification produces exact verdict `PASS_V15_LABEL_FREE_V8_DEPLOYMENT_QUALIFICATION` under its frozen gates.

## Frozen SonotaCo input

Reuse only the already-produced label-free preparation artifact from final SonotaCo r4:

- workflow run: `31354363306`;
- artifact ID: `9050107352`;
- artifact name: `orbittrace-final-sonotaco-label-free-preparation-v2`;
- artifact digest: `sha256:1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`;
- preparation verdict: `PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION`;
- base rows: 2013 = 24,899; 2014 = 20,575;
- shower truth accessed: false;
- target region retained: false;
- MAARSY scientific access: false.

Use exactly `base_2013.json` and `base_2014.json`. Do **not** use the Sugar-matched or HDBSCAN-matched subsets, because those are comparator-specific row universes rather than the detector's canonical survey input.

The historical base rows contain extra same-information transport fields. They must be projected immediately through the merged canonical event interface so the method receives only:

`id, year, sol, sun_lon, ecl_lat, vg, iau=0, complex_key=HIDDEN`.

No raw SonotaCo archive is downloaded or reparsed by this stage.

## Frozen detector

After canonical projection, use exactly the same end-to-end detector qualified on GMN:

1. exact promoted v8 label-free within-year fixed4 proposal generator (`label_free_scan_year`);
2. no calibration events and no score threshold;
3. exact v8 within-year components and 1.5-radius cross-year connected-family graph;
4. exact v8 pooled same-year centroid repair;
5. merged common v15 nominal-128 consensus with component caps `(128, 96, 64)`;
6. adaptive local episode cardinality `k=min(cap,N_local)`, fail only if `k<4`;
7. exact frozen multiplicity score and exact v15 component/consensus ordering.

No survey name may branch proposal, family, score, or ranking science.

## No-truth boundary

This applicability run accepts no known-shower mapping and no comparator output. It may emit only pre-truth engineering information:

- canonical input counts and IDs/hashes;
- label-free scan audits and proposal counts;
- recurrent family count/universe hash;
- pooled-centroid repair audit;
- observed local-episode cardinalities for each v15 component cap;
- Brown-equivalence maximum;
- component-order hashes;
- final v15 order hash;
- completion/failure reason.

It may not compute recovery, precision, MRR, F1, shower matches, Sugar/HDBSCAN comparison, or any scientific winner/loser verdict.

## Decision rule

If all source/input/firewall guards pass, at least one recurrent family is formed, every family can be scored at all three v15 component caps with `k>=4`, every Brown-equivalence difference is <=1e-10, and the final consensus order contains every recurrent family exactly once:

`PASS_V15_SONOTACO_2013_2014_ENGINEERING_APPLICABILITY`

Otherwise:

`FAIL_V15_SONOTACO_2013_2014_ENGINEERING_APPLICABILITY`

A PASS establishes only that canonical-format v15 is technically applicable to the fixed SonotaCo pair. It does not establish literature superiority, external validation, or authorization for MAARSY/OrbitTrace target access.

## Explicit exclusions

- no DMS or replacement dataset;
- no new GMN/SonotaCo/MAARSY year selection;
- no SonotaCo truth or comparator evaluation;
- no pairwise Sugar/HDBSCAN row subsets as detector input;
- no fixed-128 fallback or fabricated events;
- no v15 retuning;
- no MAARSY event access;
- no target-region or OrbitTrace target access.
