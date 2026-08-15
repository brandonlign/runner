# Final #1263 AMOS pre-data audit v3 — exact-label clean retry activation

Zero-scientific-data activation only.

This marker activates the clean v3 retry after the prior successful zero-data run `31865942127` was found to have incomplete audit coverage of an already-frozen label-transport requirement. That earlier run/artifact remains preserved and is not a scientific result. `HARDENED_FREEZE_LABEL_EXACTNESS_SUPERSESSION.md` records why its execution freeze is not authoritative for future AMOS execution.

## Exact current pins before activation

- final protocol blob `1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993`;
- original hardening freeze blob `62a6474933cecc1871449d89d59055b18ad3e802`;
- v3 hardening/no-result freeze blob `78d8ab5d657b1348f449e7af73a944c3f9acc9b1`;
- unchanged pretruth generator blob `b76d7c53ab238cd45f12027947f2098a770ba7b6`;
- repaired exact-label evaluator blob `c45e4739ea68639945b13de54f6e24dc9d870ba3`;
- corrected AST-aware source audit blob `734cc257347d6f68ce0d67f5adf874ae89e6d6d7`;
- v3 adversarial evaluator audit blob `31daaf1101bd100968829a3797b39dc856ae2a7c`;
- exact label-transport audit blob `b16778cd10cbbb7704a4ee007a14030b97e07500`;
- unchanged full synthetic pipeline selftest blob `2f9dc0495d80e1fa0c577fcbb4fec2b4dd33aecf`;
- binding clean-retry workflow blob `0fe45c38e3f15c94c688326a969c7cb3a4975f55`.

## Required clean-retry evidence

The workflow must prove, using synthetic data only:

1. AST-aware source/firewall audit PASS with no hierarchy recomputation surface in the evaluator;
2. unchanged full three-method synthetic pipeline PASS;
3. all 12 forged-pretruth tests reject before label opening;
4. all 15 frozen adversarial hardening assertions pass, including empty-catalogue binding FAIL rather than technical retry;
5. exact `SPORADIC` is accepted;
6. a valid mixed-case non-background shower code is preserved exactly;
7. ambiguous no-association aliases fail closed;
8. surrounding whitespace fails closed and is not silently normalized;
9. no scientific method, metric, gate, threshold, ranking, dataset, or firewall rule changes.

A technically valid PASS is engineering evidence only. It does not constitute AMOS external validation. A clean PASS is required before writing a new superseding execution freeze.

No provider request, AMOS scientific data, GMN, SonotaCo, ASFN, EFN, OrbitTrace target information/geometry, MAARSY, or DMS is authorized by this marker.
