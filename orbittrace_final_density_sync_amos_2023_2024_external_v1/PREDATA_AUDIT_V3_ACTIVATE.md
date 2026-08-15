# Final #1263 AMOS pre-data audit v3 activation

Zero-scientific-data activation only.

This marker activates the first v3 endpoint after the v2 static-audit engineering no-result preserved in `EVALUATOR_HARDENING_V3_FREEZE.md`.

Pinned v3 sources before activation:

- final protocol blob `1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993`;
- original hardening freeze blob `62a6474933cecc1871449d89d59055b18ad3e802`;
- v3 hardening/no-result freeze blob `78d8ab5d657b1348f449e7af73a944c3f9acc9b1`;
- unchanged pretruth generator blob `b76d7c53ab238cd45f12027947f2098a770ba7b6`;
- v3 evaluator blob `bb2a1ba553fb57e573e85df39ccad1b69fe3b541`;
- corrected AST-aware source audit blob `734cc257347d6f68ce0d67f5adf874ae89e6d6d7`;
- v3 adversarial evaluator audit blob `31daaf1101bd100968829a3797b39dc856ae2a7c`;
- unchanged full synthetic pipeline selftest blob `2f9dc0495d80e1fa0c577fcbb4fec2b4dd33aecf`;
- binding v3 audit workflow blob `238326e8ff0c7ba2bf42ca1a0d7b182ef8b1c406`.

The v3 source audit must use AST import/call targets rather than raw string matching. The adversarial audit must prove 12 forged pretruth payloads fail before label opening, 15 total hardening assertions pass, empty candidate catalogues remain valid scientific states that yield a binding FAIL rather than a technical retry, and only exact `SPORADIC` is accepted as the no-association sentinel.

No provider request, AMOS scientific data, GMN, SonotaCo, ASFN, EFN, OrbitTrace target information/geometry, MAARSY, or DMS is authorized by this marker.