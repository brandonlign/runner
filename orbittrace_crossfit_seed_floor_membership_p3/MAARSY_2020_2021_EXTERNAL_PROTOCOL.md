# OrbitTrace P3 — frozen MAARSY 2020/2021 external generalization protocol

## Status

This protocol is frozen while authoritative P3 development run `31291214704` is unresolved and before any MAARSY 2020/2021 event-level scientific value is opened for P3.

MAARSY 2020/2021 was reserved prospectively for the P2/P3 fallback lineage in PR #546. P2 failed development before its external route executed; PR #598 was closed explicitly without MAARSY 2020/2021 scientific-value access. The panel therefore remains reserved for the legitimately active P3 lineage, subject to a fresh execution-time repository-history audit.

P3 may open this panel only after:
1. exact authoritative P3 development PASS;
2. the separately frozen matched Sugar/HDBSCAN protocol returns `SPARSE_STREAM_SUPERIORITY` separately against BOTH comparators, with every required annual condition satisfied in BOTH SonotaCo 2023 and 2025; `BROAD_CATALOGUE_SUPERIORITY` alone is not sufficient;
3. execution-time history/freshness finds no earlier MAARSY 2020/2021 event-value scientific access.

Any earlier failure leaves MAARSY 2020/2021 unopened. No target-containing GMN access is authorized here.

## Claim boundary

P3 uses orbital information (`d_orb = minimum D_SH to opposite-year immutable seed`) as one of its two membership features. Therefore this external test is **not** an independent-orbit-modality validation. It is a no-retuning cross-survey transport/generalization test with an orthogonal orbital-similarity stress endpoint that is never used by P3.

A pass supports the claim that the complete frozen P3 pipeline transports to a different observing system and that its new members remain preferentially coherent under an orbital criterion not used for fitting or acceptance. It does not establish causal common origin or make the orbital endpoint independent of the underlying orbit measurements.

## Frozen survey transport

Use exactly MAARSY calendar years 2020 and 2021 from the same immutable public archive family used by the earlier MAARSY validation work.

Before first event value is read:
- verify immutable archive identity and expected source structure;
- rerun repository-history freshness for `MAARSY 2020`, `MAARSY 2021`, `data/2020/`, `data/2021/` and all known P2/P3 external artifact names;
- abort if any prior run/PR opened event-level scientific values from either year for method selection;
- freeze exact file/member enumeration and native six-column `kepler` semantics.

Transport rules are inherited without search:
- include the complete available month/member set for each frozen year exactly once;
- remove solar longitude 20°–55° before retained target-excluded event geometry/orbit values are used;
- deterministic density normalization is at most 10,000 events per frozen 10° solar-longitude bin using the smallest SHA-256 values of stable event identity;
- no random sampling, alternative cap, alternate binning, selected months, year substitution or post-outcome row filtering;
- exact promoted-v8 construction and exact P3 method are rerun on the identical retained P3 event universe;
- native orbital mapping remains `a_m, e, i_deg, omega_deg, Omega_deg, nu_deg`, with `q_AU = abs((a_m/AU_M)*(1-e))` for the P3 D_SH input;
- no shower catalogue label or target identity is used.

If the frozen P3 scientific interface cannot be transported exactly, the result is external input/integrity failure, not permission to modify P3.

## Exact P3 external execution

On the retained 2020/2021 events:
1. construct the panel-specific promoted-v8 recurrent family cores and exact v8 multiplicity order;
2. require at least 100 recurrent seed families before treating the panel as powered enough for a membership-generalization test; otherwise return `INCONCLUSIVE_P3_MAARSY_EXTERNAL_POWER_N` without changing the panel;
3. execute exact P3 cross-year two-view science unchanged, including two features `[d_obs,d_orb]`, ±5° candidate/background windows, >=128 negatives/direction, five deterministic family folds, held-out seed-floor rule, 0.10 negative-tail ceiling, final all-family logistic model and strict joint responsibility >0.5;
4. freeze and hash all family cores/order, cross-fit models/held-out score digests/reliability decisions, final model, proposal/conflict payload, P3 memberships and deterministic control identities before the external stress endpoint is computed;
5. no external endpoint may feed back into P3 membership, family rank or any threshold.

## Deterministic controls frozen before stress evaluation

For every P3-added event, define the eligible control pool before computing the stress metric:
- same assigned family and same target year;
- event was in that family's frozen ±5° local non-seed candidate window;
- event is not an original v8 seed and was not assigned by P3 to any family;
- event has a valid native orbit under the frozen parser.

For each added event select one control, without replacement within family/year when possible, by the smallest SHA-256 of `P3-MAARSY-CONTROL|family_id|year|event_id`. If fewer controls than additions exist, use all available controls and record the shortage; power requires at least 200 controls overall. No D_SH, Drummond value, probability, responsibility, label or outcome enters control selection.

Controls are a local-background reference rather than a perfectly feature-matched counterfactual. Report this limitation explicitly.

## Orthogonal post-freeze orbital stress metric

The primary stress endpoint is the Drummond orbital dissimilarity `D_D` (Drummond 1981), not the Southworth–Hawkins `D_SH` used by P3.

For two orbits, compute

`D_D^2 = ((q1-q2)/(q1+q2))^2 + ((e1-e2)/(e1+e2))^2 + (I/180°)^2 + (((e1+e2)/2)*(theta/180°))^2`,

where `I` is the angle between orbital planes and `theta` is the angle between lines of apsides/eccentricity vectors. Implement the geometry deterministically from the native orbital elements and source-audit it before first MAARSY 2020/2021 value access. P3 never uses `D_D` during training, gating, proposal scoring, conflict resolution or ranking.

For each addition/control assigned to family `f` in year `y`, define its stress score as minimum `D_D` to the immutable opposite-year v8 seed orbits of family `f`.

Do not search a `D_D` cutoff. The primary endpoint is continuous and relative to preselected controls.

## Frozen power requirements

The powered external membership test requires all of:
- >=100 recurrent promoted-v8 seed families on the retained external panel;
- >=30 families with at least one valid-orbit P3 addition;
- >=200 valid-orbit P3 additions total;
- >=200 valid deterministic controls total;
- >=90% of frozen P3 additions have a valid native orbit;
- >=90% of selected controls have a valid native orbit;
- both calendar years contribute >=50 valid additions;
- both calendar years contribute >=50 valid controls.

If source/integrity passes but any power requirement fails, return `INCONCLUSIVE_P3_MAARSY_2020_2021_EXTERNAL_POWER`. Do not lower the requirement or try another panel/subsample after seeing values.

## Frozen external scientific gates

On the powered panel all must pass:

1. **Continuous effect:** pooled median nearest-opposite-year-seed `D_D` for P3 additions <= 0.75 × pooled median for deterministic controls.
2. **Distributional separation:** one-sided Mann–Whitney U test for additions having lower `D_D` than controls has p <= 0.01. Use the exact pooled valid frozen scores once; no multiple threshold search is performed.
3. **Family consistency:** among families with >=3 valid additions and >=3 valid controls, at least 70% have median addition `D_D` lower than median control `D_D`; at least 20 such powered families must exist.
4. **Year consistency:** the median addition `D_D` is lower than the median control `D_D` separately in both 2020 and 2021.
5. **No pathological concentration:** no single family contributes >20% of all valid additions; if it does, the external result fails the generalization gate rather than dropping that family.
6. **P3 transport integrity:** all exact P3 pretruth, cross-fit, seed immutability, responsibility, truth/target firewall and no-retuning assertions pass.

A pass is `PASS_P3_MAARSY_2020_2021_EXTERNAL_GENERALIZATION`.

A powered scientific failure is `FAIL_P3_MAARSY_2020_2021_EXTERNAL_GENERALIZATION` and blocks final target access. An integrity/interface failure is reported separately and authorizes only equivalence-preserving technical repair if the exact preregistered P3 science can still be recovered.

## Required reporting

Report at minimum:
- retained events/year/bin and archive/parser integrity;
- recurrent v8 family count;
- reliable/unreliable P3 family-direction counts;
- P3 additions by year/family and assignment concentration;
- valid-orbit addition/control counts and fractions;
- pooled/year/family `D_D` summaries;
- median ratio, one-sided Mann–Whitney statistic/p-value, powered-family consistency fraction;
- every power, integrity and scientific gate;
- explicit statement that P3 uses D_SH and that D_D is a distinct but correlated orbital-similarity stress metric, not an independent measurement modality.

## Target firewall

Solar longitude 20°–55° remains excluded throughout this external validation. No OrbitTrace coordinate, member ID, target identity, historical target rank/recovery, target activity profile, withheld exact target reference or target-containing output may enter the run.

Only exact P3 development PASS + `SPARSE_STREAM_SUPERIORITY` against BOTH Sugar and HDBSCAN in BOTH SonotaCo 2023 and 2025 + `PASS_P3_MAARSY_2020_2021_EXTERNAL_GENERALIZATION` may satisfy P3's prerequisites for a separately frozen final target-containing Stage A.
