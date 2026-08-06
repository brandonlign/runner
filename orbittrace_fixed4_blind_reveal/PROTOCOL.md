# Frozen reveal of the OrbitTrace blind catalogue scan

## Inputs

- blind scan workflow run: `31074826765`;
- blind scan artifact: `8958042095`;
- blind scan artifact ZIP SHA-256: `3ce72dde553cf58c6d4b9e734c29558a0f2bbefee664ba98189f4e90e821c596`;
- blind scan payload SHA-256: `9c8c5f2d3bf1a94b7b01eabbbae670007fe1d23f0e933035eb5b4667d13fb02e`;
- canonical artifact: `8814798136`;
- canonical artifact ZIP SHA-256: `716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5`.

The blind artifact contains 780 ranked cross-year families and was frozen before the canonical member table was retrieved.

## Immutable reveal rules

`FULL_BLIND_ORBITTRACE_REDISCOVERY` requires one family to:

- rank within the top 25;
- span at least four years;
- contain at least 16 canonical members;
- contain at least four canonical members in each of at least three years.

`PARTIAL_BLIND_ORBITTRACE_RECOVERY` requires one family to:

- rank within the top 100;
- span at least three years;
- contain at least 12 canonical members;
- contain at least four canonical members in each of at least two years.

Otherwise the result is `NO_BLIND_ORBITTRACE_RECOVERY`.

The reveal may not merge families, change their order, rescore events, alter identifiers, or use enrichment significance as a replacement decision rule. Hypergeometric enrichment and family-count Bonferroni correction are descriptive only.

## Claim boundary

A full result would justify a blind independent rediscovery claim for the final detector. A partial result establishes substantial blind recovery but does not justify saying the detector fully rediscovered OrbitTrace under the frozen standard. Neither result changes the literal exploratory chronology, formal IAU status, or the unresolved distinct-stream-versus-branch interpretation.
