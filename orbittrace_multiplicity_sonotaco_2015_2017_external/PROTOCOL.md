# OrbitTrace sparse-support multiplicity — fresh SonotaCo 2015/2017 external validation

## Status

Prospectively preregistered **before the first SonotaCo 2015 or 2017 meteor-archive access**.

This is a fresh cross-survey catalogue-ranking validation of the sparse-support multiplicity architecture. It is not a Boolean rescue detector, not a target recovery, and not an OrbitTrace reveal stage.

OrbitTrace remains blinded. No event in the closed solar-longitude interval 20°–55°, and no OrbitTrace coordinates, members, activity, identity, or target-consistency criterion, may enter this stage.

## Freshness and parser prerequisites

Archive access is forbidden unless all source-only prerequisites pass exactly:

1. corrected full-repository freshness audit run `31198545147`, artifact `9001841755`, verdict `PASS_CORRECTED_SONOTACO_2015_2017_REPO_FRESHNESS_AUDIT`;
2. validated SonotaCo-2023 parser source audit run `31198923927`, verdict `PASS_SONOTACO_2023_PARSER_SOURCE_AUDIT`;
3. source-only SonotaCo 2015/2017 parser transport run `31199214174`, artifact `9002098911`, verdict `PASS_SONOTACO_2015_2017_SOURCE_ONLY_PARSER_TRANSPORT`;
4. generated parser SHA-256 values are exactly:
   - 2015: `88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3`;
   - 2017: `bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3`.

The spent SonotaCo-2016 positive control was correctly detected by the freshness audit. The predecessor audit failure from run `31198105470` remains preserved as an implementation-classification failure.

## Fixed fresh survey panel

The panel is exactly **SonotaCo 2015 + SonotaCo 2017**.

The only authorized archive URLs are:

- `https://sonotaco.jp/doc/SNMv3/015a.zip`
- `https://sonotaco.jp/doc/SNMv3/017a.zip`

The only authorized annual members are:

- 2015: `015a/_U2_20150101_S.csv`
- 2017: `017a/_U2_20170101_S.csv`

If an archive is unavailable, malformed, or does not contain the exact preregistered member, the result is an integrity failure/inconclusive transport result. No alternate member or year may be searched after data access begins.

## Frozen parser and blindness behavior

The generated parsers inherit the validated SonotaCo parser behavior exactly:

- the closed 20°–55° solar-longitude interval is excluded before the shower field is read;
- all validated header, finite-value, geometry, `ncam >= 2`, coordinate-conversion, ESV-background, native-label, and GMN-MDC mapping rules remain fixed;
- the archive SHA, member SHA, row count, parser diagnostics, and all source URLs are recorded as provenance;
- parser integrity gates must all pass.

For proposal generation, labels are stripped after parsing:

- every retained labelled or sporadic meteor contributes only geometry plus a hidden event ID;
- candidate-scan records use `iau=0` and `complex_key="HIDDEN"`;
- the fixed4 calibration reservoir contains only parser-defined post-ESV sporadic meteors, with labels hidden;
- native shower labels are retained separately and may be consulted only after all candidate families and all four ranking orders have been completed.

Thus known-shower labels cannot steer candidate proposals or multiplicity ranking.

## Immutable proposal generator

Proposal generation is the exact frozen fixed4 support-normalized scanner with raw source SHA-256:

`fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`.

All scientific constants remain exact:

- candidate scale 4°;
- local window 10°;
- episode size 128;
- 128 fixed4 calibration negatives per supported bin;
- 10° Mondrian bins;
- 64-neighbor shortlist and 128-neighbor audit;
- minimum anchor count 2;
- maximum 512 retained quartets per bin;
- minimum component events 4;
- minimum component quartets 2;
- family-link radius 1.5;
- minimum family years 2.

The frozen family linker treats years categorically: components may link only across different years and only when centroid distance is at most 1.5. It contains no adjacent-year or year-gap weighting, so the nonconsecutive 2015/2017 panel changes no family rule.

Before the first archive access, the scanner is transported only by setting:

- `YEARS = (2015, 2017)`;
- `CORPUS = "sonotaco-2015-2017-sparse-support-multiplicity-external"`;
- `RANKING_VARIANTS` back to the exact raw fixed4 tuple beginning with `persistence`.

The new corpus string is a preregistered deterministic dataset identity used by the frozen calibration seed; it is not selected after seeing performance.

## Primary ranking signal

For every recurrent fixed4 family and each of 2015 and 2017:

1. use that year's frozen family centroid;
2. form the exact deterministic 10° local window;
3. select the exact 128 nearest events under the frozen wavelet geometry;
4. compute exact frozen multi-anchor wavelet energy v3 and the independent Brown comparator;
5. require Brown equivalence within `1e-10`;
6. compute the scale-free multi-anchor multiplicity

`M = (E_v3 / B_Brown)^2`.

No multiplicity p-value is introduced.

### Frozen rankings

Primary **multiplicity recurrence** ranking:

1. larger `min(M_2015, M_2017)`;
2. larger `sqrt(M_2015 * M_2017)`;
3. stable family ID.

Fixed comparators:

- unchanged fixed4 `persistence`;
- Brown amplitude recurrence, larger minimum yearly Brown score then stable family ID;
- total-v3 recurrence, larger minimum yearly v3 energy then stable family ID.

There is no RRF, Boolean union, threshold search, weight search, p-value search, or rank-endpoint search.

## Cross-survey ranking endpoint

The development catalogue had exactly 197 recurrent families and used top 100. To preserve the **same development rank quantile** under a survey with a different family count, define before data access:

`K(N) = ceil(100 * N / 197)`

implemented exactly as integer arithmetic:

`K = (100*N + 196) // 197`.

This is the only primary top-rank endpoint. Literal top-100 is not a scientific gate on this external panel.

The endpoint is sufficiently powered only if both:

- `K >= 30`;
- `N - K >= 30`.

If either fails, the external validation is **inconclusive for ranking power**, not a scientific failure.

## Known-shower evaluation

Labels remain hidden until all four family rankings exist.

An eligible mapped known shower must have:

- at least 8 labelled meteors across the two-year panel;
- at least 4 labelled meteors in 2015;
- at least 4 labelled meteors in 2017.

For each eligible label, choose its best family by:

1. F1;
2. precision;
3. overlap count;
4. stable family ID.

A match qualifies only with:

- at least 4 exact labelled members;
- precision at least 0.50.

For every ranking report:

- eligible and qualified known-shower counts;
- recovery at `K`;
- mean reciprocal rank;
- median rank;
- macro F1;
- mean dominant-label precision among the top `K` families.

Family-rank Spearman correlations and top-`K` overlaps are descriptive only.

## Validity / power gates

The scientific result is interpretable only if all are true:

1. all exact freshness, source, parser-transport, and fixed-source SHA guards pass before archive access;
2. exactly the two preregistered archive URLs and annual members are used;
3. both transported parser integrity panels pass completely;
4. the 20°–55° exclusion remains source-verified before shower-label access;
5. both years contain at least 1,000 scan events and at least 1,000 sporadic calibration events after parsing;
6. each year supports at least 24 frozen fixed4 calibration bins;
7. every retained recurrent family contains both 2015 and 2017 components;
8. every retained family receives an exact 128-event local episode in both years;
9. maximum independent Brown-equivalence difference is at most `1e-10`;
10. the scaled endpoint has at least 30 families above/in the head and at least 30 families below it (`K >= 30` and `N-K >= 30`);
11. at least 30 known showers qualify under the frozen evaluation rule;
12. all four rankings cover the identical family universe and all four evaluations cover the identical qualified-label universe.

If gates 10 or 11 fail, verdict is `INCONCLUSIVE_MULTIPLICITY_SONOTACO_EXTERNAL_POWER`.
If any other integrity gate fails after archive access, verdict is `FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_INTEGRITY`.

## Prospective scientific pass rule

If every validity/power gate passes, the fresh external validation passes only if all are true:

1. multiplicity recovery at `K` is at least **one qualified shower greater** than Brown recurrence recovery at `K`;
2. multiplicity recovery at `K` is at least `ceil(0.90 * fixed4 persistence recovery at K)`;
3. multiplicity dominant-label precision at `K` is at least **0.50**.

MRR, median rank, correlations, and overlap diagnostics cannot rescue or overturn these frozen gates.

## Consequences

A pass freezes sparse-support multiplicity as the independently validated catalogue-ranking architecture. **It still does not authorize OrbitTrace reveal.**

After a pass, a separate final target-free discovery-application protocol must be committed before the 20°–55° interval is opened. That protocol must freeze the final catalogue years/survey, proposal generation, ranking endpoint/output depth, and the criterion for calling a blindly generated family OrbitTrace-consistent.

A scientific failure or underpowered/integrity result is preserved exactly. It does not authorize retuning this panel or accessing OrbitTrace.
