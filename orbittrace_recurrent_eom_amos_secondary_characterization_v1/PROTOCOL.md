# OrbitTrace recurrent-EOM — secondary AMOS 2023/2024 external characterization v1

## Status

**FROZEN PRE-DATA, PRE-AMOS, AND WITHOUT CHANGING THE PRIMARY #1268 ENDPOINT.**

This supplement exists only to answer whether the selected **paper method**, recurrent-EOM HDBSCAN v1, generalizes on the same single pristine AMOS 2023/2024 receipt already governed by PR #1268.

It does not select a new primary AMOS method, does not create a second external chance, does not reopen labels, and does not alter any candidate catalogue. The existing #1268 evaluator already freezes ordinary HDBSCAN, recurrent-EOM, and density-synchronous recurrent-EOM before labels and writes ordinary/recurrent/density-sync annual metrics into one post-freeze result. This supplement consumes **only that result JSON** after the single primary truth evaluation has completed.

## Immutable method

Recurrent-EOM HDBSCAN v1 remains exactly the paper method selected in PR #1269.

Exact recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Exact recurrent development runner Git blob:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

No recurrent membership, rank, hierarchy, HDBSCAN parameter, metric, threshold, or tie rule may change.

## Immutable upstream AMOS contract

The sole upstream scientific endpoint remains PR #1268:

- selected primary method: density-synchronous recurrent-EOM v1;
- exact AMOS years: 2023 and 2024;
- inclusive protected exclusion: `[20.0,55.0]` solar longitude;
- complete ordinary, recurrent, and density-sync candidate catalogues frozen before labels;
- exact hardened label evaluator Git blob: `c45e4739ea68639945b13de54f6e24dc9d870ba3`;
- labels opened once only after the full pretruth hash freeze;
- no replacement survey, AMOS rerun, method switch, or post-result parameter search.

This supplement may execute only on the exact post-freeze result emitted by that endpoint. It never accepts AMOS geometry or label files directly.

## Scientific question

On pristine AMOS 2023/2024, does exact recurrent-EOM preserve the preregistered fixed-budget quality criteria that originally justified it over ordinary HDBSCAN EOM on GMN?

## Frozen external-characterization gate

Use the **same recurrent-EOM development gate dimensions** as the original GMN selection, transferred without modification to AMOS 2023 and 2024.

For **each** year, recurrent-EOM versus ordinary HDBSCAN must satisfy all five no-regression conditions:

1. recovered@50 is not lower;
2. recovered@100 is not lower;
3. mean top-100 dominant precision is not lower;
4. historical recovered-only MRR is not lower;
5. median top-500 fragmentation is not higher.

Two global conditions are also mandatory:

6. recovered@100 is **strictly higher in at least one** of AMOS 2023 or 2024;
7. the pretruth reports the recurrent-EOM mechanism active versus ordinary EOM (different selected-node set and/or frozen order).

Thus the gate contains **12 mandatory booleans**: `5 × 2` annual preservation gates plus `2` global gates.

Return exactly one token:

- `PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION`, or
- `FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_CHARACTERIZATION`.

A valid FAIL is binding. Do not run another external survey, alter recurrent-EOM, switch the characterization gate, or reinterpret a mechanism-inactive result as positive generalization.

## Reporting-only metrics

Also preserve, without using them to rescue the gate:

- full-catalogue qualified/recovered showers;
- recovered@25;
- recovered@500;
- exact ordinary and recurrent annual metrics already emitted by #1268.

The original paper-method selection explicitly prioritized fixed-budget ranking/recovery rather than universal improvement of every catalogue-wide metric. This external characterization keeps the same standard rather than adding a favorable metric after outcome.

## Interpretation

### PASS

A PASS supports the statement that the frozen recurrent-EOM paper method reproduced its preregistered fixed-budget no-regression/strict-improvement behavior on a pristine external survey under the same one-shot AMOS receipt.

It does not establish universal superiority across all meteor networks or all literature algorithms.

### FAIL

A FAIL means pristine cross-survey generalization of recurrent-EOM is **not established**. The historical negative ASFN result remains part of the evidence, and no new external-survey hunt is authorized.

## Relationship to the primary density-sync AMOS endpoint

This secondary result is scientifically independent of the primary density-sync PASS/FAIL token in the sense of interpretation, but not an independent data chance: both are adjudicated from the **same** single frozen AMOS pretruth and single post-freeze label opening.

Possible outcomes are reported honestly:

- both pass;
- density-sync passes while recurrent-EOM fails;
- recurrent-EOM passes while density-sync primary fails;
- both fail.

No outcome changes which bytes were tested.

## Firewall

At freeze time:

- AMOS provider request sent: false;
- AMOS transfer received: false;
- AMOS event-level scientific access: false;
- AMOS shower-association access: false;
- protected OrbitTrace target access: false;
- SonotaCo new scientific access: false;
- ASFN/EFN new event-level access: false;
- MAARSY/DMS scientific access: false;
- post-result parameter search: false;
- replacement external survey authorized: false.
