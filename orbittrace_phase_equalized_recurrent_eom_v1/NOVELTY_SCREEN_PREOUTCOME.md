# Phase-intensity-equalized recurrent-EOM v1 — pre-outcome novelty screen

**Timing:** recorded while the first frozen GMN development run was still computing and before its scientific outcome was available. This note does not alter the method, gate, or execution bytes.

## Narrow conclusion

The literature screen did **not** identify a prior meteoroid-stream clustering method that applies the exact frozen construction used here: a protected-gap-preserving pooled empirical cumulative-intensity reparameterization of accessible solar longitude, followed by an otherwise unchanged HDBSCAN/recurrent-EOM detector.

This supports treating the construction as a potentially novel **meteor-stream methodology component**, subject to a broader formal literature review before any paper-level priority claim.

It does **not** support claiming that cumulative-distribution transforms or density homogenization in clustering are new in general.

## Relevant prior meteor methods

### Sugar et al. (2017), *Meteor Shower Detection with Density-Based Clustering*

Uses DBSCAN with a geocentric feature/distance construction including solar longitude, geocentric speed, and Sun-centered radiant geometry. The reviewed method does not empirical-CDF-equalize solar longitude before clustering.

Reference: Sugar, Moorhead, Brown & Cook, arXiv:1702.02656.

### Peña-Asensio & Ferrari (2025), *Meteoroid stream identification with HDBSCAN unsupervised clustering algorithm*

Applies standard HDBSCAN to geocentric/orbital feature vectors and studies EOM versus leaf extraction/minimum cluster size. The reviewed method does not use the frozen empirical solar-phase intensity transform.

Reference: arXiv:2507.01501.

### Peña-Asensio & Sánchez-Lozano (2024), *Statistical Equivalence of Metrics for Meteor Dynamical Association*

Reports that meteor-association accuracy depends on solar longitude, with a pronounced degradation around approximately 180 degrees coincident with increased meteoroid-background activity. This provides independent physical/statistical motivation for testing a solar-phase background-intensity reparameterization; it is not a source of the specific frozen transform.

Reference: arXiv:2405.03308.

### Galligan (2003), *Radar meteoroid orbit stream searches using cluster analysis*

Explicitly discusses temporal/solar-longitude structure and variable detection rates as a difficulty in constructing representative meteoroid backgrounds, and explores separate-year hierarchical strategies. It does not describe the exact pooled empirical phase-CDF transformation used here.

Reference: MNRAS 340, 899–907, DOI 10.1046/j.1365-8711.2003.06348.x.

## General clustering prior art that limits the novelty claim

Zhu, Ting, Carman & Angelova (2018), *CDF Transform-and-Shift: An effective way to deal with datasets of inhomogeneous cluster densities* (arXiv:1810.02897), explicitly proposes CDF-based feature-space transformation to homogenize inhomogeneous cluster densities before applying clustering algorithms.

Therefore a scientifically defensible novelty statement, if the method ultimately warrants one, is **not** “we invented CDF density equalization.” The potentially novel contribution is narrower:

> applying a physically constrained, protected-gap-preserving, pooled empirical solar-phase intensity coordinate to meteoroid-stream HDBSCAN and combining it with annual recurrent-EOM extraction under a blind development/validation protocol.

## Claim discipline

Until a formal broader search is complete, do not write “first ever,” “new mathematical transform,” or “novel CDF clustering.” Prefer wording such as:

- “we introduce a meteor-specific phase-intensity equalization step”;
- “to our knowledge, we did not identify prior meteor-stream clustering work using this exact construction”;
- “the contribution is the meteor-specific physical constraint and integration with recurrence-aware hierarchical density clustering, not the general probability-integral-transform concept.”

No result from the active GMN run may alter this novelty characterization or the method itself.
