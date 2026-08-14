# AMOS 2023/2024 public bulk-data recheck — 2026-08-14

**Classification: metadata/acquisition audit only. Scientific AMOS event access: NONE.**

## Purpose

Recheck whether a public bulk data product now exists that can satisfy the already-frozen AMOS 2023/2024 recurrent-EOM external-validation contract without direct provider outreach.

This audit does not authorize changing the requested years, fields, sample definition, blind interval, method, comparator set, evaluator, or gates.

## Public sources checked

The search covered current public/indexed AMOS and research-data surfaces using the 2026 AMOS network paper title/DOI and combinations of `AMOS`, `meteor`, `2023`, `2024`, `trajectory`, `catalogue`, and `dataset`, including:

- current Comenius University / AMOS project and publication pages;
- Tóth et al. (2026), *AMOS global meteor network: Instrumentation, procedures, accuracy validation and results*, Icarus 454, 117086, DOI `10.1016/j.icarus.2026.117086`;
- indexed web/search surfaces for Zenodo, Figshare, Mendeley Data and CDS/VizieR-style catalogue records;
- general indexed searches for the exact DOI/title combined with `dataset` / `data repository` / `2023 2024 trajectories`.

The publisher full-text endpoint itself returned HTTP 403 to the automated client, so no claim is made about any non-indexed text hidden behind the publisher interface.

## Findings

1. The 2026 AMOS network paper and current project material confirm that the present AMOS pipeline performs automated meteor detection/reduction and multi-station trajectory/orbit determination, so the already-frozen retained-event geometry request remains technically plausible.
2. The public searches did **not** identify a documented bulk release containing the complete solved AMOS 2023/2024 multi-station population with the staged fields required by the frozen protocol.
3. Publicly discoverable AMOS-related scientific datasets/papers found during the search are older, specialized, selected, or case-study products and are not substitutes for the complete 2023/2024 solved population. They must not be substituted after seeing this availability result.
4. No public source discovered in this audit provides the frozen three-layer separation of blind index -> retained geometry -> post-pretruth shower associations.

## Binding acquisition conclusion

`NO_DISCOVERABLE_COMPLIANT_PUBLIC_AMOS_2023_2024_BULK_RELEASE_2026_08_14`

This is an availability conclusion, **not** evidence that no institutional/private AMOS export exists.

The exact staged provider request in `DATA_REQUEST_READY_WITH_COMPARATORS.md` remains the scientifically clean next acquisition route.

## No-substitution rule

This audit does not authorize:

- using another AMOS year pair;
- using a quality-selected/spectral/fireball-only AMOS sample;
- reconstructing the needed population from papers or case studies;
- scraping individual event pages;
- deriving missing geocentric quantities from rounded orbit values;
- changing recurrent-EOM or comparator requirements to fit a smaller public product;
- opening shower associations before pretruth freeze.

## Firewall

- `amos_event_rows_accessed=false`
- `amos_shower_labels_accessed=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `orbittrace_target_access=false`
