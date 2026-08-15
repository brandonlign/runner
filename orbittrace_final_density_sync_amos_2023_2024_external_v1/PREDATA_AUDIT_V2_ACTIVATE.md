# Final #1263 AMOS hardened pre-data audit v2 activation

Zero-scientific-data activation only.

This marker activates the evaluator-hardening audit frozen before implementation in `EVALUATOR_HARDENING_FREEZE.md`.

Pinned v2 sources:

- protocol blob `1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993`;
- hardening freeze blob `62a6474933cecc1871449d89d59055b18ad3e802`;
- unchanged pretruth generator blob `b76d7c53ab238cd45f12027947f2098a770ba7b6`;
- hardened evaluator blob `07ece6d0ef8a63b1f2523c59b9b5fefb1485f198`;
- v2 source audit blob `3ea3d88fe7a411ea04bdbc2b6ea8710f8f7260c3`;
- adversarial evaluator audit blob `095a4c6b784f40e885e50f211e9db481f2b470c4`;
- unchanged full synthetic pipeline selftest blob `2f9dc0495d80e1fa0c577fcbb4fec2b4dd33aecf`;
- v2 audit workflow blob `7019bed19ae434805b2bb061344867274d16c58a`.

The audit must prove the valid synthetic pipeline still evaluates unchanged and that forged source pins, HDBSCAN pins, order hashes, non-retained candidate IDs, overlapping candidate memberships, duplicate retained IDs, annual-EOM reconstruction, and mechanism flags are each rejected before nonexistent label paths can be opened.

No provider request, AMOS scientific data, GMN, SonotaCo, ASFN, EFN, target information/geometry, MAARSY, or DMS is authorized.