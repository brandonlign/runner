# Binding locked-RRF OrbitTrace reveal result

The first valid end-to-end frozen reveal completed successfully in GitHub Actions run `32204257498` at execution commit `d35e249332e29d39dcfdb1c4c298b6be7763f618`.

Exact verdict: `PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY`.

Frozen inputs and source remained unchanged:

- blind scan run: `31112651984`;
- blind scan artifact: `8973803775`;
- blind scan artifact ZIP SHA-256: `1c26dc06193eb2119a0e181d9a85c22c18b09da8316fe6679754cb554ca29d34`;
- blind scan inner payload SHA-256: `c55e3db626df21faede809cf6b74f808b0c5c13a56672682f6d09f6b11c5d0b3`;
- canonical artifact: `8814798136`;
- canonical artifact ZIP SHA-256: `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`;
- frozen reveal source blob: `eff6c77421f83afe1951212ba6548601403f5120`;
- frozen reveal source SHA-256: `9bb8108c012b4681c4bfacdfbdfcc703b52ba2b1cc7dd38e8a2cd076eda811fd`.

Selected blind family `G88cc88b1e28a`:

- locked-RRF rank: `46 / 766`;
- family years: `4`;
- family events: `39`;
- exact canonical overlap: `29 / 95`;
- overlap by year: `2022: 5`, `2023: 4`, `2024: 0`, `2025: 15`, `2026: 5`;
- precision: `0.7436`;
- canonical recall: `0.3053`.

The pre-frozen partial rule passed: rank <=100, at least 3 years, at least 12 exact canonical members, and at least 4 members in at least 2 years. The stronger full rule did not pass because it required rank <=25 (and the selected family has rank 46).

Frozen reveal evidence artifact: `9348567823`, artifact ZIP SHA-256 `a05f6d501af2dd1db70b5ecb027d28b9c47d34b838221ba7784dc62daa1cc666`.

Scientific interpretation: this supports a target-free blind partial recovery of OrbitTrace by the separately frozen fixed-4°/locked-RRF pipeline. It does not justify post-reveal reranking or tuning to force the full gate, and it is not a result of the recurrent-EOM paper flagship.
