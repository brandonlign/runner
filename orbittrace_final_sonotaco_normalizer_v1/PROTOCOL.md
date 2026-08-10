# Final SonotaCo 2013/2014 label-free normalizer freeze v1

## Purpose

Freeze the candidate/comparator row-normalization contract before either reserved SonotaCo 2013 or 2014 scientific archive is opened. This source is based only on previously spent SonotaCo annual-U2 schema knowledge (validated 2016 and 2023 interfaces). It contains no archive URL/hash/row count for the reserved years and cannot access them.

## Fixed schema rule

The annual science CSV must normalize to the exact historically validated 45-field U2 header. A single trailing empty header field is permitted because that exact transport artifact was already observed in historical SonotaCo annual files; no other missing/renamed/reordered field is accepted.

If 2013 or 2014 does not satisfy this schema, the scientific normalizer fails closed. Only a separately source-audited structural transport repair may then be considered, using header/row-structure information only and before retaining any scientific event value. The scientific cuts below cannot change.

## Firewall and row cuts

For each physical data row:

1. decode only `soldeg`;
2. normalize finite solar longitude modulo 360°;
3. discard the closed interval **20°–55°** immediately;
4. only after that exclusion, decode RA, Dec, geocentric speed and camera count;
5. retain only finite geometry with `0 <= RA < 360`, `-90 <= Dec <= 90`, **5 <= Vg <= 75 km/s**, and **ncam >= 2**;
6. convert RA/Dec to ecliptic longitude/latitude using the already-frozen geometry helper and set Sun-centered longitude to wrapped `(lambda_ecl - solar_longitude)`;
7. emit only `id, year, sol, sun_lon, ecl_lat, vg, iau=0, complex_key=HIDDEN`.

The `shower` field is never read from a data row. No truth mapping, IAU shower code, target identity, orbital element, uncertainty value, or target-region geometry enters this normalizer.

The Vg 5–75 km/s bound is inherited from the active hard-v8/P19/P20 scanner rather than the broader historical SonotaCo fixed4 episode parser. It is therefore part of the final candidate/common-row scientific universe and cannot be widened after final-test access.

## Stable row identity

Event IDs are generated from an arbitrary caller-supplied prefix plus physical CSV row number. Year is carried as an explicit field; no downstream transport may infer year from the ID string.

## Downstream fairness

The final candidate, Sugar, catalogue HDBSCAN, and post-output truth evaluator must all consume the same exact retained-row manifest for each pairwise final-test universe as already frozen by the final comparison policy. This normalizer does not itself expose or consume truth.

## Activation boundary

Passing the synthetic/source audit does **not** authorize opening SonotaCo 2013/2014. Final-test scientific access remains forbidden until GMN M0/M2 adjudication has completed, the exact integrated candidate executable is frozen, and that executable is explicitly declared `FINAL_FOR_LITERATURE_TEST`.

MAARSY 2020/2021 and OrbitTrace/20°–55° remain sealed.
