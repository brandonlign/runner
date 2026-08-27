# Final SonotaCo 2013/2014 shared label-free manifest — v2

## Purpose

Freeze the candidate/comparator row-normalization contract before either reserved SonotaCo 2013 or 2014 scientific archive is opened. The exact annual-U2 schema is known only from already-spent historical SonotaCo interfaces. This source contains no reserved-year URL/hash/row count and cannot access either final-test archive.

The shared manifest **carries, without selecting on,** every raw field required by the frozen final methods: OrbitTrace geometry, Sugar RA/Dec/Vg uncertainties and convergence angle, and catalogue-HDBSCAN physical-quality fields. Final OrbitTrace M0/#839 ignores comparator-only fields. No known-shower/background truth is exposed before output freeze.

## Fixed schema

The annual science CSV must normalize to the exact historically validated 45-field U2 header. One trailing empty header field is permitted because that exact transport artifact was already observed historically. Any other schema change fails closed before scientific-row retention.

## Firewall and base row cuts

For each physical data row:

1. decode **only** `soldeg`;
2. normalize finite solar longitude modulo 360°;
3. discard the closed interval **20°–55°** immediately;
4. only after that exclusion may any other scientific column be decoded;
5. retain the base shared row only when `0 <= RA < 360`, `-90 <= Dec <= 90`, **5 <= Vg <= 75 km/s**, and **ncam >= 2**;
6. convert RA/Dec to ecliptic geometry with the already-frozen helper and form wrapped Sun-centered longitude.

The shower field is never read.

## Shared fields carried after the firewall

Every retained base row carries:

- stable `id`, explicit `year`, `sol`, `sun_lon`, `ecl_lat`, `vg`;
- raw `ra`, `dec`;
- raw Sugar uncertainty inputs `ra_sd`, `dec_sd`, `vg_sd`;
- native `q`, `e`, `peri`, `node`, `inc`;
- native convergence angle `qc` from U2 `qcdeg`;
- `ncam`;
- hidden placeholders `iau=0`, `complex_key=HIDDEN`.

Missing/nonfinite comparator-only values are represented as null and do **not** remove an otherwise valid base row. This prevents the shared parser from silently choosing one comparator's structural universe.

## Pairwise structural eligibility

Before truth is opened:

- **Sugar pairwise universe** applies exactly the label-free structural/quality requirements frozen in #820 after the shared base cuts: finite nonnegative `ra_sd`, `dec_sd`, and `vg_sd`; **strict `qc > 15°`**; and **`vg_sd <= 0.10 * vg + 1.0 km/s`**. Zero reported uncertainty is permitted as a finite zero-width Gaussian; negative uncertainty is not.
- **HDBSCAN pairwise universe** applies exactly the frozen algorithm/source quality requirements after the shared base cuts: finite `qc`, `vg_sd`, `q`, and `e`; `qc >= 15°`; `vg_sd / vg <= 0.10`; **`0 <= e <= 1.0`**; and **`0 < q <= 1.0 AU`**.
- **OrbitTrace M0/#839** uses the base geometry rows and ignores uncertainty/orbit/convergence-angle fields.

For each comparator, the exact pairwise common-row universe is the intersection of the final candidate's frozen structural eligibility and that comparator's frozen structural eligibility. No pairwise structural filter may depend on shower truth, method score, target identity, or post-output performance.

The normalizer implements the Sugar and HDBSCAN predicates separately. They are deterministic functions of carried label-free fields and do not mutate the base manifest.

## Stable identity

Event IDs are caller-supplied prefix plus physical CSV row number. Year is carried explicitly; downstream code may not infer year from the ID string.

## Same-information fairness

For each comparator/year, candidate and comparator receive the exact same pairwise retained event IDs and the same shared raw-field records. An algorithm may ignore fields it does not use, but no hidden truth/background designation or unavailable proxy may be supplied selectively.

## Activation boundary

GMN methodology selection is complete: **M0/#839 is final and M2 is a permanent no-go**. Passing this normalizer's synthetic/source audit still does **not** authorize SonotaCo 2013/2014 access.

Final-test scientific access remains forbidden until the pair-portable #839 generator passes the predeclared GMN operational-equivalence gate, including exact discrete structure and exact final deployment-order invariance, and the fail-closed final-test authorization contract in `orbittrace_final_sonotaco_execution_v1/` is satisfied.

The external endpoint remains **MAARSY 2022**, with **MAARSY 2021 only as permanently unlabeled recurrence support**. MAARSY event-level scientific values and OrbitTrace/20°–55° remain sealed.