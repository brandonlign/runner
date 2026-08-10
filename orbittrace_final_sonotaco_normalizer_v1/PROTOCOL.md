# Final SonotaCo 2013/2014 shared label-free manifest — v2

## Purpose

Freeze the candidate/comparator row-normalization contract before either reserved SonotaCo 2013 or 2014 scientific archive is opened. The exact annual-U2 schema is known only from already-spent historical SonotaCo interfaces. This source contains no reserved-year URL/hash/row count and cannot access either final-test archive.

V2 fixes one preaccess fairness omission in v1: the shared manifest now **carries**, without selecting on, the raw uncertainty fields required by frozen Sugar and the orbital elements that an already-frozen M2/P12 membership layer would require if M2 is ultimately promoted. OrbitTrace, Sugar, and HDBSCAN still consume only their frozen predeclared fields. No algorithm receives a field that is hidden from another algorithm on the same pairwise row universe.

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
- native orbit inputs `q`, `e`, `peri`, `node`, `inc`;
- `ncam`;
- hidden placeholders `iau=0`, `complex_key=HIDDEN`.

Missing/nonfinite uncertainty or orbit values are represented as null and do **not** remove an otherwise valid base row. This prevents the shared parser from silently choosing one comparator's structural universe.

## Pairwise structural eligibility

Before truth is opened:

- **Sugar pairwise universe** additionally requires positive finite `ra_sd`, `dec_sd`, and `vg_sd`, because the frozen uncertainty-clone algorithm cannot faithfully operate without them.
- **HDBSCAN pairwise universe** uses the base geometry rows and ignores uncertainty/orbit fields.
- **OrbitTrace M0** uses the base geometry rows and ignores uncertainty/orbit fields.
- If **M2** is promoted, its separately frozen transport may additionally require complete finite `q,e,peri,node,inc`; that requirement must be applied symmetrically to the OrbitTrace-vs-comparator common-row universe before outputs and before truth.

No pairwise structural filter may depend on shower truth, method score, target identity, or post-output performance.

## Stable identity

Event IDs are caller-supplied prefix plus physical CSV row number. Year is carried explicitly; downstream code may not infer year from the ID string.

## Same-information fairness

For each comparator/year, candidate and comparator receive the exact same pairwise retained event IDs and the same shared raw-field records. An algorithm may ignore fields it does not use, but no hidden truth/background designation or unavailable proxy may be supplied selectively.

## Activation boundary

Passing the synthetic/source audit does **not** authorize SonotaCo 2013/2014 access. Final-test scientific access remains forbidden until:

1. GMN M0/M2 adjudication is complete;
2. the exact integrated candidate executable is frozen;
3. the candidate is explicitly declared `FINAL_FOR_LITERATURE_TEST`.

MAARSY 2020/2021 and OrbitTrace/20°–55° remain sealed.
