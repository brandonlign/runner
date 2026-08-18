# Locked-RRF OrbitTrace reveal execution request

This branch exists only to execute the already-frozen locked-RRF reveal against the immutable successful blind-scan artifact.

Frozen inputs:

- blind scan workflow run: `31112651984`;
- blind scan artifact: `8973803775`;
- blind scan artifact digest: `sha256:1c26dc06193eb2119a0e181d9a85c22c18b09da8316fe6679754cb554ca29d34`;
- reveal source branch/base: `agent/orbittrace-fixed4-locked-rrf-reveal-source-audit` at `42b039bf6065b5f914b858da543395d6374fe373`;
- frozen reveal source blob: `eff6c77421f83afe1951212ba6548601403f5120`;
- frozen reveal source SHA-256 from prior source audit: `9bb8108c012b4681c4bfacdfbdfcc703b52ba2b1cc7dd38e8a2cd076eda811fd`;
- reveal gates: full rank <=25 with >=4 years, >=16 exact canonical members, and >=4 members in >=3 years; partial rank <=100 with >=3 years, >=12 members, and >=4 members in >=2 years.

No detector, ranking, family, matching, threshold, or reveal rule may change on this execution branch. The only scientific action authorized is applying the already-frozen reveal to the successful immutable blind ranking.
