# Direct-finalize recovery source-equivalence audit

Source-only audit performed before using any recovered scientific verdict.

Compared:

- exact exported frozen v6 source SHA-256 `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`;
- recovery implementation `orbittrace_v6_direct_finalize_recovery/finalize_year.py`.

The audit asserted the recovery post-exact path contains the exact frozen scientific operations for:

1. Brown proposal p-value via `empirical_upper_pvalue(proposal_brown_score, proposal_cal[bin])`;
2. v3 p-value via `empirical_upper_pvalue(v3_score, v3_cal[bin])`;
3. fixed4 p-value via `empirical_upper_pvalue(fixed4_score, fixed4_cal[bin])`;
4. v3 detection at the frozen `BASE_ALPHA = 0.05`;
5. fixed4 rescue detection at frozen `RESCUE_ALPHA = 1/129` with the original `+1e-15` comparison tolerance;
6. exact primary anchor conflict tuple `(p_v3, -v3_score, p_fixed4, proposal_anchor_id)`;
7. exact rescue anchor conflict tuple `(p_fixed4, p_v3, -fixed4_score, anchor_id)`;
8. exact per-bin cap `MAX_COMPONENTS_PER_BIN * 8`;
9. repaired exact primary component call `component_records_track_v6(..., "v3")`;
10. repaired exact rescue component call `component_records_track_v6(..., "fixed4_rescue")`.

The corresponding unqualified scientific expressions were asserted to exist in the exact frozen source. The two repaired component-builder calls are the already-source-audited implementation repair whose repaired-source SHA-256 is `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`.

The recovery makes no proposal selection, nearest-neighbor regeneration, threshold choice, scientific score approximation, membership change, family-ranking change, label-dependent choice, or target-region access.

This audit is source-only and does not itself establish a scientific PASS/FAIL. Scientific classification remains contingent on all runtime identity checks and the unchanged repaired-main gates.
