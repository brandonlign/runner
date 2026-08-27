# OrbitTrace literature-comparator audit — 2026-08-09

## Purpose

Document why the permanent matched literature stage uses Sugar uncertainty-aware DBSCAN and catalogue HDBSCAN as its two required direct comparator families. This audit is comparator-selection evidence only; it does not change any final-test data, thresholds, gates, candidate architecture, or target firewall.

## Direct-comparator inclusion rule

A method is a primary direct comparator if it is a published, target-free/unsupervised method whose scientific output is a catalogue or partition of meteors into candidate meteor showers / meteoroid streams from event-level meteor data. Methods that only assign events to an already-known shower, estimate false-positive rates for a separate association rule, model shower dynamics, or characterize a previously selected stream are useful context but are not direct catalogue-discovery comparators.

## Required comparator 1: Sugar et al. (2017)

Glenn Sugar, Althea Moorhead, Peter Brown, and Bill Cooke, **“Meteor shower detection with density-based clustering,”** *Meteoritics & Planetary Science* 52, 1048–1059 (2017), DOI `10.1111/maps.12856`.

Why it remains required:

- target-free DBSCAN catalogue discovery in geocentric meteor-observation space;
- explicitly incorporates observational uncertainty through 1,000 cloned catalogues;
- merges recurrent cluster realizations and obtains probabilistic meteor membership;
- was designed to recover both strong and weak shower detections rather than only perform known-shower assignment.

The final OrbitTrace comparator interface therefore preserves the scientifically relevant Sugar architecture while enforcing the project’s same-information rule on the exact matched row universe.

## Required comparator 2: Peña-Asensio & Ferrari (2025)

Eloy Peña-Asensio and Fabio Ferrari, **“Meteoroid Stream Identification with HDBSCAN Unsupervised Clustering Algorithm,”** *The Astronomical Journal* 170, 140 (2025), DOI `10.3847/1538-3881/adec8c`.

Why it is the strongest recent direct catalogue comparator identified in this audit:

- published 2025 unsupervised catalogue-scale meteoroid-stream identification;
- evaluates HDBSCAN on the CAMS Meteoroid Orbit Database v3.0;
- compares multiple physically motivated feature vectors, including GEO and ORBIT;
- evaluates EOM and leaf cluster selection and multiple minimum cluster sizes;
- reports that EOM/GEO gives the strongest agreement and that weak/less-active showers remain a principal challenge.

For the final same-information comparison, OrbitTrace uses the faithful catalogue-HDBSCAN formulation already frozen in repository governance, without any truth-dependent row filter.

## Relevant methods not promoted to mandatory direct comparators

### Shober & Vaubaillon (2024) KDE false-positive framework

Patrick M. Shober and Jeremie Vaubaillon, **“A generalizable method for estimating meteor shower false positives”** (2024), arXiv `2404.08507`.

This is scientifically relevant for significance / contamination estimation, but its primary contribution is a KDE-based false-positive estimation framework applied around similarity-discriminant association rules. It is not a standalone target-free catalogue-discovery algorithm producing an alternative full shower partition from the event set, so it is not a like-for-like primary matched comparator.

### Classical D-criterion / single-linkage stream searches

These remain important historical baselines, but their limitations on large, biased, uncertainty-rich catalogues are well documented and the later Sugar/HDBSCAN methods directly address the same catalogue-discovery problem with modern density clustering. They therefore do not supersede the two mandatory comparators above.

## Search conclusion

A current literature search through 2026-08-09 identified no later published general target-free meteoroid-stream catalogue-discovery method that clearly supersedes the 2025 HDBSCAN study as a direct matched comparator. The final literature requirement therefore remains strongest when it requires superiority against **both**:

1. uncertainty-aware Sugar/DBSCAN; and
2. modern catalogue HDBSCAN.

This is a search conclusion, not a proof that no other method exists. If a materially stronger directly comparable published method is identified before `FINAL_FOR_LITERATURE_TEST`, it must be evaluated for inclusion before the permanent SonotaCo test is opened.

## Firewall

This audit uses literature only. It accesses no SonotaCo 2013/2014 scientific values, no MAARSY scientific values, no OrbitTrace target coordinates/identity/members, and no target-region events or results. The solar-longitude 20°–55° firewall is unchanged.
