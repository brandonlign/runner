# Phase-marginal mutual-star support: July development benchmark

Status: development-only benchmark on the now-retired July 2026 data. This PR cannot authorize application to GhostStream or any discovery claim.

## Motivation

PR #48 established that nested phase-adaptive conformal calibration generalized to an untouched month, but its raw score included relative solar longitude in within-window member similarity. Meteor-shower members can remain coherent in Sun-centered radiant and geocentric speed while spreading across solar longitude. Solar longitude should therefore define the local search window and calibration phase without necessarily penalizing member-to-member similarity inside that window.

## Candidate

For each 128-event window:

1. compute pairwise distance using only Sun-centered ecliptic radiant longitude, radiant latitude, and geocentric speed, with fixed scales 2 degrees, 2 degrees, and 2 km/s;
2. for every event, form a four-star consisting of the event and its three nearest neighbors;
3. measure each star's maximum pairwise feature distance;
4. negate the mean of the eight smallest star diameters.

The eight-star support endpoint was selected on the retired July development screen because it improved overall weak-shower AUROC and k=6/k=8 discrimination relative to truncation at three or five stars. No new significance threshold or calibration rule is introduced.

## Frozen development run

- exact PR #48 July data artifact;
- exact 38-shower positive panel and 1,024 negative windows;
- exact 512-window inner bank, 512-window outer bank, KNN=128 local normalization, and independent outer conformal rank;
- eight positive replicates per shower/member count;
- fixed k in {4,6,8,12};
- existing July blocks and GhostStream blind interval unchanged.

This run is used only to decide whether the candidate merits a separately frozen untouched 2018 confirmation. July is retired and cannot serve as confirmation again.
