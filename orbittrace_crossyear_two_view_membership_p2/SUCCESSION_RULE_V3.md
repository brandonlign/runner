# P2 unified succession rule v3

## Purpose

This addendum changes **only method-selection routing**, not P2 science. It is frozen before any P1, C1-LF, or P2 scientific result that could activate the new routes below.

Canonical P2 remains exactly the source-audited two-view cross-year membership method at SHA-256 `f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb`, with every feature, training rule, threshold, rank, development gate, label firewall, and target exclusion unchanged.

## Why an addendum is necessary

P2 was originally frozen when P1 was the only planned membership successor, so its executor currently recognizes only exact P1 scientific no-go. The later pre-result v6/v6-LF precedence freeze created a second legitimate branch: a development-viable v6-LF can fail literature, activate C1-LF, and consume C1-LF without ever executing P1. Leaving P2 dependent on a P1 artifact would make that branch dead-end for an administrative reason unrelated to P2 science.

The routing rule therefore follows the **active preregistered method chain**, not a requirement that every inactive predecessor be executed.

## Authorized P2 activation states

P2 may execute once, without modification, after either route A or route B is satisfied.

### Route A — P1 branch

The existing route remains unchanged:

- canonical ordinary v6 has a genuine scientific development no-go;
- v6-LF has a genuine scientific development no-go;
- exact frozen P1 is executed and returns `FAIL_PROBABILISTIC_MEMBERSHIP_P1_NO_GO` with its integrity gates satisfied.

### Route B — fully label-free branch

This route is available only if v6-LF first passed development and therefore legitimately bypassed P1. P2 becomes the next successor after C1-LF is objectively non-promotable under one of its already-frozen stages:

1. C1-LF development returns `FAIL_V6_LF_CORE_PROBABILISTIC_MEMBERSHIP_C1_NO_GO`; or
2. C1-LF passes development but its frozen matched-literature comparison returns `NO_LITERATURE_SUPERIORITY`; or
3. C1-LF passes development and literature superiority but its prospectively frozen external/generalization gate returns a scientific FAIL; or
4. that external/generalization gate returns `POWER_INCONCLUSIVE` under its frozen pretruth power rules, leaving C1-LF without the independent generalization evidence required for promotion.

A technical execution failure, missing artifact, corrupted artifact, failed integrity/firewall check, or incomplete run is **never** an authorized Route-B state. Such failures permit only infrastructure-equivalent repair of the same upstream stage.

## Artifact verification requirement

Any future P2 execution wrapper implementing Route B must verify the complete upstream chain, not merely marker text. At minimum it must prove:

- exact v6-LF development PASS identity;
- exact v6-LF `NO_LITERATURE_SUPERIORITY` if C1-LF was activated through that branch;
- exact C1-LF source identity and development artifact;
- the terminal C1-LF non-promotion artifact appropriate to cases 1–4 above;
- target interval 20°–55° remained excluded throughout method development;
- no OrbitTrace target information was accessed.

The wrapper must accept only exact frozen verdict strings and artifact schemas. It must reject mixed, duplicate, or technically failed lineages.

## No outcome-based method switching

This addendum does not permit comparing P1 and C1-LF scores and choosing the better predecessor. Only the branch fixed by the v6/v6-LF precedence protocol may run. P2 is reached only after the legitimately active predecessor chain fails to earn promotion under its already-frozen gate.

P2 remains a fresh target-excluded scientific test. No prior target result, OrbitTrace coordinates/members/identity, target-region event, or final-search result may enter P2 training, development, literature comparison, external validation, or routing.
