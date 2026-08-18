# Zero-data source + synthetic audit result

Latest authoritative audit: GitHub Actions run `32194732274` from audit child PR #1353.

Verdict:

`PASS_RECURRENT_EOM_AMOS_SECONDARY_SOURCE_AUDIT`

The audit verified:

- frozen protocol Git blob `84ed2264583e5af23a53a19a51546eead82ac274`;
- frozen adjudicator Git blob `1350dc5df5c1af292721906fc85fb8179757867f`;
- synthetic audit Git blob `8a63facd5b0a751d7f1ff56a4a67d968a2299501`;
- Python compilation of both executable audit files;
- exact upstream #1268 hardened evaluator pin `c45e4739ea68639945b13de54f6e24dc9d870ba3`;
- exact recurrent-EOM kernel pin `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- exact recurrent development runner pin `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- the single-AMOS-endpoint/no-second-external-chance contract;
- exact 12-gate PASS/FAIL token definitions.

The same audit then exercised the complete adjudicator on four zero-data synthetic cases:

1. canonical 12/12 PASS;
2. 11/12 FAIL when strict recovered@100 improvement is absent;
3. 11/12 FAIL from a small annual top-100 precision regression;
4. 11/12 FAIL when the recurrent mechanism is inactive despite otherwise positive metrics.

All four behaved exactly as frozen.

Earlier run `32194565446` / PR #1352 independently passed the source-only version of the audit and remains preserved as earlier engineering provenance. Run `32194732274` supersedes it as the complete source + synthetic gate audit.

No AMOS geometry, AMOS labels, protected OrbitTrace data, SonotaCo data, ASFN/EFN event-level data, MAARSY, or DMS scientific data were accessed. The supplement remains dormant until the single #1268 AMOS endpoint has a compliant transfer and completes its one post-freeze truth evaluation.
