# OrbitTrace pooled-year-centroid v8 — AMOR 1996+1998 one-shot external validation

## Status and purpose

This is the first scientific AMOR access for the v8 architecture. AMOR 1990–1999 passed the full-repository freshness audit before any archive access. A subsequent structure-only audit, permitted only after v8 passed development, opened all annual ZIPs without numeric scientific-token conversion and selected **1996 + 1998** by the preregistered rule: the two years with the largest opaque record counts, tie earlier.

No AMOR scientific value has been interpreted before this protocol is frozen.

## Immutable inputs

Selected archives and members from the structure-only artifact:

- 1996: `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1996.zip`; SHA-256 `d2444969fff5f99bd74f94b5742f07f36a6ce5dec040adf4832bf7e8ea116de1`; member `amor1996.csv`.
- 1998: `https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcamor1998.zip`; SHA-256 `f65a562d37d55d0d751d30213350dc333a3620717d3236436a35154e73c3f054`; member `amor1998.csv`.
- Exact header in both years: `DB,IC,Yr,Mn,Day,LS,RA,dRA,DECL,dDECL,Vg,Vh,q,e,a,i,arg,nod`.
- The structure-only audit found width-17 malformed rows in both selected years. Before numeric decode, parser policy is frozen to **accept exactly 18-token data rows and drop every other width without repair or inference**.

There is no alternate AMOR year pair or malformed-row repair.

## Blind discovery fields and order of access

For accepted width-18 rows:

1. Solar longitude `LS` is the first scientific field converted to a number.
2. Rows with `20° <= LS <= 55°` are discarded immediately.
3. Only after that exclusion may nominal year/month and discovery geometry be read.
4. Discovery uses only `LS`, `RA`, `DECL`, and `Vg`, transformed to the exact frozen Sun-centered radiant-speed geometry.
5. `q/e/i/arg/nod` are not interpreted until **all candidate families and all four rankings are frozen**.
6. No shower label or supplied target identity exists in candidate generation or ranking.

Event identity is `AMOR|year|member|physical_row_number`; the density sampler hashes only this fixed identity.

## Density normalization

Identical to the frozen SAAMER external standard:

- fixed 10° solar-longitude bins;
- retain at most 10,000 eligible events per bin;
- if a bin exceeds 10,000, retain the 10,000 smallest SHA-256 identity hashes;
- no random seed, alternative cap, or density-dependent tuning.

## Detector and family architecture

Inherited unchanged from passed v8:

- exact label-free fixed4 structural proposal engine from v6;
- shortlist 64, audit shortlist 128;
- anchor multiplicity >=2;
- max 512 retained quartets per 10° bin;
- component gates >=4 events and >=2 quartets;
- cross-year connected-family links at frozen centroid radius 1.5;
- multiple same-year components remain permitted inside a connected recurrent family;
- per-family-year centroid is recomputed from the union of unique same-year component events using the source-audited statistic: circular mean `sol`/`sun_lon`, median `ecl_lat`/`vg`;
- exact 128-event local episodes;
- multiplicity `M=(multi-anchor-v3-energy / Brown-peak)^2` is the primary ranking;
- Brown, total-v3, and label-free persistence remain frozen comparators;
- no threshold, radius, cap, pooling-rule, weight, RRF, or endpoint search.

## Post-ranking orbital corroboration

The exact frozen SAAMER external evaluator is reused rather than redefined.

After rankings freeze, only family member rows are reread for `q,e,i,arg,nod`. Orbital corroboration is:

- exact frozen Southworth–Hawkins `D_SH` implementation;
- single-link graph at `D_SH < 0.05`;
- a qualifying orbital component must contain >=4 members from 1996 and >=4 from 1998;
- qualifying component size / full family event count must be >=0.50;
- one family is counted once if such a component exists.

Orbits validate frozen families; they never generate or rank them.

## Endpoint and power

Let `N` be recurrent families and `Q` be orbitally corroborated families. Let `K=min(100,N)`.

Power gates, inherited unchanged from the SAAMER external protocol:

- `N >= 100`;
- `Q >= 30`.

If either power gate fails, the result is **inconclusive for external power**. It is not a method failure and may not justify changing the AMOR panel, K, or thresholds.

## Scientific pass gates

Only if both power gates pass:

1. multiplicity top-K corroborated families >= Brown top-K + 1;
2. multiplicity top-K corroborated families >= `ceil(0.90 * persistence top-K corroborated)`;
3. multiplicity top-K hypergeometric enrichment p <= 0.05.

All must pass. Failure of any scientific gate is a genuine external failure for this v8 formulation. No AMOR-driven retuning or second AMOR year pair is permitted.

## Decision boundary

A powered external pass authorizes freezing the final target-free full-GMN v8 discovery scan while OrbitTrace remains unrevealed to that scan. It does not itself establish OrbitTrace recovery.

Only after the final discovery ranking is immutable may a separate reveal compare its candidates with the canonical OrbitTrace members/solution.
