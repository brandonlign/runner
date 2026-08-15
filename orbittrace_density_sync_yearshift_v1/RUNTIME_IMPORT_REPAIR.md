# Runtime import repair after pre-data technical no-result

Workflow run `31897558825` is permanently classified as a technical no-result.

The run passed all source pins, the zero-truth year-shift synthetic audit, the frozen GMN runtime-utility verification, the frozen v8 support-artifact verification, and the exact #1263 binding-evidence verification. It then stopped during import of the already-frozen GMN runtime dependency chain with:

`ModuleNotFoundError: No module named 'multi_anchor_energy_v3'`.

The failure occurred before the GMN catalogue parser ran, before any successor candidate was scored, before any successor order or prelabel was written, and before hidden known-shower truth was opened. The uploaded artifact contains no scientific result.

The only authorized repair is to restore the exact historical `multi_anchor_energy_v3.py` runtime module already required by the frozen GMN loader:

- source commit: `d8258581af143308495bd97bedcc142abbbd951a`;
- Git blob: `2ba4835db23f8f623cdd28d0a4e6113b7954ecb2`.

This module is a runtime dependency only. The year-shift scientific protocol, statistic, GEO6 representation, exact #1263 candidate universe, ranking rule, strong `+2` recovered@100 gate, protected `[20°,55°]` exclusion, and all truth/firewall rules remain byte-for-byte unchanged.

The next technically valid run remains the first binding scientific outcome.