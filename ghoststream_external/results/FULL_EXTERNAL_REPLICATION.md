# GhostStream full external-catalog replication

**Verdict:** `FROZEN_EXTERNAL_REPLICATION_PASSED_IN_SONOTACO`

The complete IAU MDC 2026 CAMS v3, SonotaCo, and EDMOND yearly catalogs were evaluated with the unchanged GMN-derived template and preserved decision gates. No external-source parameter was refit.

## CAMS

- Role: independent replication
- Valid seasonal rows: **64,830**
- Frozen-template members: **9**
- Counts by year: `{'2011': 2, '2012': 4, '2014': 1, '2015': 1, '2016': 1}`
- Active years: `[2011, 2012]`
- Activity p: **0.0100121**
- Shifted-window p: **0.0204082**
- Orbit median D: **0.05630196189174284**
- Orbit q90 D: **0.1164213849035731**
- Orbit-null p: **0.0001**
- Preserved gate passed: **False**

## SonotaCo

- Role: independent replication
- Valid seasonal rows: **52,565**
- Frozen-template members: **11**
- Counts by year: `{'2007': 1, '2009': 3, '2010': 1, '2013': 1, '2018': 1, '2020': 1, '2022': 2, '2023': 1}`
- Active years: `[2009, 2022]`
- Activity p: **0.000630978**
- Shifted-window p: **0.0204082**
- Orbit median D: **0.02997685132088911**
- Orbit q90 D: **0.05632443032431853**
- Orbit-null p: **0.0001**
- Preserved gate passed: **True**

## EDMOND

- Error: `no usable archive`

## Interpretation boundary

A CAMS or SonotaCo pass is independent external-network replication under the frozen GMN solution. EDMOND is supplementary because its contributing observations can overlap other video networks. Any failed gate is retained without threshold relaxation.

