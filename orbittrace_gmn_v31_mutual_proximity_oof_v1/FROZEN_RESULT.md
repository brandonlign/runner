# Frozen result — GMN v31 Mutual-Proximity local-geometry OOF successor v1

Binding run: `31649753150`
Binding job: `94291250659`
Execution head: `0232c086f40cb9be7e054e6f7663142aed163c09`
Artifact: `9162182072`
Artifact digest: `sha256:308c174c097803d547a59ba57aaa21a2b8ed12cfe23596b9d0422a502404b071`
Result JSON SHA-256: `141faba345532421467e18c728209a60e81023a7457580134ed71c1ae03e0fe2`
Prelabel JSON SHA-256: `deb0d8737431f59820d003b45e680d7d151e18c6da830ae7ae24579a7f97d50d`

Verdict: `FAIL_GMN_V31_MUTUAL_PROXIMITY_OOF`

## Binding comparison against frozen passed parent

Parent benchmark:
- recovered@100: `66`
- recovered@50: `41`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified families: `95`

Mutual-Proximity fused successor:
- recovered@100: `63` — FAIL (`>66` required)
- recovered@50: `46` — PASS
- recovered@25: `25` — nonbinding diagnostic
- recovered@500: `95` — nonbinding diagnostic
- top-100 dominant precision: `0.6698037113321298` — FAIL
- MRR: `0.051120234196879666` — PASS
- qualified families: `95` — PASS

The successor therefore failed 2 of 5 binding gates. The improvement in early-prefix recovery and MRR does not rescue the loss in recovered@100 and top-100 precision.

## Mechanism diagnostic

The preregistered hubness motivation did not receive strong support from nearest-reference concentration. Across the five folds, the maximum number of held-out queries sharing one raw-Euclidean nearest reference was `2,4,3,3,4`; under empirical Mutual Proximity it was `3,4,2,3,3`. MP therefore did not consistently reduce the already-low nearest-reference concentration.

## Permanent closure

The exact empirical Mutual-Proximity v1 successor is permanently rejected. Do not rescue it with inequality changes, denominator changes, pseudocounts, parametric Gaussian/Gamma MP, independence approximations, local scaling, k changes, feature/fold/diversity/fusion changes, or hybrids with failed representation mechanisms. Any future successor must be independently motivated and separately frozen before its first outcome.

Firewall remained clean: SonotaCo 2013/2014 was not accessed by this binding GMN run; protected 20°–55° target information/events, MAARSY, and DMS were not accessed.
