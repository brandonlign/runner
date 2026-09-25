# SonotaCo 2025 survey-native prefix audit

Status: frozen before recomputing any mapped-label support count under the new survey-native rule. This is aggregate-only and cannot compute a detector score.

## Scientific boundary

PR #58 remains killed under its exact-token canonical mapping. Its aggregate output established that SonotaCo labels use survey-native forms such as `GEM_JA`, `PER_JA`, and `SDA_JA`. SonotaCo 2025 is therefore consumed development data and may be used for a separately prospective survey-native formulation. SonotaCo 2024 remains value- and label-blinded as the reserved confirmation panel established by PR #63.

## Frozen label rule

Apply one rule identically to every nonbackground token:

- uppercase and trim whitespace;
- `SPO`, blank tokens, and tokens without ASCII letters are background;
- a labeled token is syntactically valid only when it matches exactly `^([A-Z0-9]{3})_JA$`;
- its canonical code is exactly the captured three-character prefix;
- match that code against the unchanged eligible-code mapping in the exact PR #14 GMN/MDC audit;
- syntactically valid prefixes absent from that mapping remain unmatched;
- every other nonbackground token is invalid/unmatched.

No suffix list, per-shower alias, fuzzy match, prefix-length choice, case-specific exception, or manual mapping is permitted.

## Pinned inputs

- SonotaCo archive URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip`;
- archive SHA-256: `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`;
- member: `025a/_U2_20250101_S.csv`;
- member SHA-256: `30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7`;
- expected rows: 36,826;
- exact PR #14 audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

## GhostStream blindness

Remove solar longitude 20.0° through 55.0° inclusive before any label, support, geometry, uncertainty, or complex count. No GhostStream radiant, speed, orbit, membership, event list, score, or local background enters this audit.

## Frozen readiness rules

- geometry requires finite solar longitude, RA, Dec, and geocentric speed within physical bounds;
- reservoir readiness additionally requires `Ncam >= 2`;
- uncertainty completeness requires nonnegative finite `ra sd`, `de sd`, `vg sd`, and `Er`;
- a supported matched code requires at least 20 reservoir-ready rows;
- supported complex count is computed from the unchanged PR #14 complex key attached to each supported matched code.

## Frozen continuation gates

Every gate must pass:

1. exact SonotaCo archive and member hashes;
2. exact GMN/MDC audit hash;
3. all required unique fields;
4. all 36,826 published rows structurally parsed with zero malformed rows;
5. geometry completeness outside the blind interval at least 0.95;
6. reservoir-ready background at least 10,000;
7. uncertainty completeness at least 0.90;
8. at least 99% of nonbackground label rows match the single frozen `XXX_JA` syntax;
9. at least 80% of syntactically valid reservoir-ready labeled rows map to an eligible frozen canonical code;
10. at least 20 supported matched codes;
11. at least 10 supported complex keys.

## Continuation rule

A complete pass authorizes only a separately frozen SonotaCo 2025 scientific development screen of the coverage-normalized 10° Mondrian four-clique mechanism, adapted to the survey's documented fields and this exact label rule. It does not authorize 2024 access, GhostStream application, catalogue scanning, or a discovery claim.

Any failed gate kills this exact prefix formulation. No syntax relaxation, alternate suffix, code alias, support threshold, complex threshold, blind interval, quality filter, or year may be changed after execution.