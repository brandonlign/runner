# Terminal synthesis AMOR audit-key correction

Frozen after terminal-synthesis run `31229833146` and **before any corrected synthesis execution**.

That run passed the frozen source checks, complete repository branch-name inventory, and all eight authoritative artifact hash checks. The synthesis then passed every promoted-v8, SAAMER, and AMOR N/Q/integrity/power assertion until it reached one source-schema typo:

- synthesizer spelling: `orbit_read_audit`
- exact serialized AMOR result key: `orbital_read_audit`

The already-hash-verified final AMOR result contains:

`orbital_read_audit["orbital_elements_interpreted_only_after_rank_freeze"] == true`

The remaining UKMON, Harvard, FRIPON, and Hissar result schemas were also inspected from their already-frozen result artifacts solely to verify the synthesizer's existing key assertions; they match as written.

The correction is restricted to one exact source-token replacement from `orbit_read_audit` to `orbital_read_audit`. The frozen `synthesize.py` input blob is `11f7cb3fb4e372701f5da40f62102eeafa5f1c5a`; a correction script must refuse to run unless that exact source blob is present and the typo occurs exactly once.

No result value, N/Q count, integrity gate, power gate, method parameter, panel status, power floor, pass/fail rule, successor rule, target-reveal rule, or OrbitTrace blinding boundary is changed. No catalogue, raw meteor, or new scientific value is accessed by this correction.
