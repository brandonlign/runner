# AMOS multi-method supplementary contract — zero-data audit result

**Engineering result: POSITIVE. Scientific result: NONE.**

The retained-ID-only comparator supplement contract passed its synthetic fail-closed audit before any AMOS event-level scientific value or shower association was available to this branch.

- workflow run: `31847583469`
- artifact: `9236426826`
- artifact digest: `sha256:37ed11086a96fae05f75a33457a8138f3acd7f0fd1d055895ef7c89785bac2a2`
- execution head: `dfa2b5c4a3b400cfcc385be1b73831fe6a2cf32b`
- verdict: `PASS_AMOS_MULTIMETHOD_PREDATA_CONTRACT_SELFTEST_V1`

The audit established on synthetic-only rows that:

- unknown/non-retained IDs, duplicate IDs, extra columns, truth-bearing columns, and non-finite supplied comparator quantities fail closed;
- the frozen strict Sugar convergence-angle predicate and catalogue-HDBSCAN predicate produce the intended distinct pairwise universes;
- blank comparator-only quantities affect only supplementary comparator eligibility and do not alter the primary AMOS sample;
- every row delivered to recurrent-EOM contains exactly `id,year,sol,sun_lon,ecl_lat,vg`;
- `ra_sd_deg`, `dec_sd_deg`, `vg_sd_km_s`, `convergence_angle_deg`, `q_au`, and `e` are absent from recurrent-EOM projections after eligibility is determined;
- no AMOS truth, protected target information, MAARSY, or DMS was accessed.

This engineering PASS does not authorize AMOS scientific execution. It only establishes that the already-frozen multi-method supplement can be implemented without leaking comparator-only fields into recurrent-EOM.
