# ASFN hash-header repair semantic audit — binding result

**POSITIVE engineering only. No ASFN archive/event/shower access in this audit.**

Binding run: `31850078483`

Binding artifact: `9237225355`

Artifact digest: `sha256:7f5d9cea4686e74b1d059366c2c8d73b71b0d29b91eb6fa3e3b0234f7cabeb9b`

Result SHA-256: `212a52b402187d0bc20c85dc50ba9d0b6b52cbe5126398d9ca7b6b87ffa49ff2`

Verdict:

`PASS_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT`

All preregistered semantic checks passed. In particular:

- the frozen ordinary header remains recognized;
- the previously unrecognized exact `# + FIELDS` header becomes recognized;
- changed or truncated hash-prefixed headers fail closed;
- representative 44-token data-like, blank, and arbitrary non-header inputs retain the frozen parser behavior;
- `FIELDS`, `IDX`, `YEARS`, `BLIND`, archive/readme identities, and HDBSCAN size constants remain unchanged;
- no non-`header_or_record` module object identity changed when the wrapper was installed;
- the wrapper contains no network/archive read, HDBSCAN operation, recurrent-EOM operation, or scientific-parameter reassignment.

This PASS authorizes only a separately frozen scientific retry that executes the byte-identical frozen ASFN validation runner through the already-existing wrapper blob `0e5fce5b04959ec45c42bb22ed477e48bdc31bde`. It authorizes no change to the scientific protocol, years, representation, blind interval, HDBSCAN settings, recurrent-EOM objective, ranking, truth semantics, evaluator, or gate.

The original technical no-result `31834974219` remains preserved and is not a scientific endpoint.
