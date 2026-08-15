# Final #1263 AMOS transport-reuse audit activation

Zero-scientific-data activation only.

This marker activates a rerun of the exact historical synthetic transport audits on the final-selected #1263 AMOS pre-data branch.

Pinned historical transport sources from unexecuted AMOS infrastructure head `1fb8f68b84bc200545a23cb5a216baa7e0fa0f09`:

- blind receipt blob `9fed803aa09f03f779610eaff5304251bbf21020`;
- blind receipt selftest blob `9331c3c01a0f9e78f46a9a7e512427c0863bcdde`;
- canonical transform blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- canonical adapter blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`;
- mapping/GEO6 selftest blob `d0ff80a520bf1861f935dd83afaa313fe56a9986`.

Current audit workflow blob: `bf2a44773022b426fe34da0b713c20eae9eb78d8`.

The audit must prove again that solar-longitude boundaries 20.0 and 55.0 degrees are excluded inclusively, wrong-year/duplicate/extra-column blind-index inputs fail closed, the canonical RA/Dec/Vg adapter maps exactly into the frozen GEO6 arithmetic, and protected/non-retained geometry fails closed.

No provider request, AMOS event row, AMOS label, GMN, SonotaCo, ASFN, EFN, OrbitTrace target information, protected-target-region geometry, MAARSY, or DMS is authorized by this marker.