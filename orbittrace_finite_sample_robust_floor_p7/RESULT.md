# P7 authoritative development result

Authoritative workflow: `31295871142`
Artifact: `orbittrace-finite-sample-robust-floor-membership-p7-development` (`9033122516`)
Artifact digest: `sha256:705b53bfca6a743af73d16852da3e880c28a650008c646982ff8af7560394f81`

Verdict: `FAIL_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_NO_GO`

Exact v8 -> P7 endpoints:
- qualified matches: 95 -> 92 (sole substantive failure)
- recovery@100: 58 -> 58
- macro F1: 0.1736657194465356 -> 0.4095287141152058
- top-100 dominant precision: 0.6884631112636006 -> 0.6928914189509618
- large-shower mean recall: 0.06738386922850433 -> 0.2727007940342044
- large-shower mean precision: 0.9204974210270073 -> 0.8855828524298333
- assigned nonseed events: 24,847
- proposal events: 24,902
- conflicted proposal events: 222

P7 affected 50 reliable directions with at least 19 held-out recurrent seeds, but the second-order-statistic floor removed only 98 P6 assignments and did not restore any of the three qualified matches. All integrity/truth-firewall gates passed. No comparator, external-validation, target-region event, or OrbitTrace target information was accessed.

This exact P7 configuration is permanently a scientific no-go.
