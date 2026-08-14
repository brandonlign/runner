# Consensus-EOM HDBSCAN v1 — binding GMN development result

**Verdict: NEGATIVE — permanently closed.**

Binding run: `31843289411`

Binding job: `94904522020`

Binding head: `53e9edb0529cb19b13b7562de93cfe75e3f3ea65`

Artifact: `9235191749`

Artifact digest:

`sha256:b6da1d47e052c11c344e082a840359e128999d2d7e86145c1c95bfb5372e8320`

Binding token:

`FAIL_CONSENSUS_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`

The zero-truth identity audit had already passed before this run, and the scientific mechanism was frozen before outcome. The binding run completed successfully as an execution on the exact target-excluded 2022+2023 GMN development pool (315,024 + 423,658 = 738,682 events), using recurrent-EOM HDBSCAN v1 as the parent.

## Binding comparison

### 2022

Recurrent-EOM parent:

- candidates: 2,097 pooled (shared parent count)
- recovered @25: 22
- recovered @50: 45
- recovered @100: 89
- recovered @500: 193
- qualified matches: 236
- top-100 dominant precision: 0.7856486012780942
- MRR: 0.022498269587309373
- median top-500 fragmentation: 1.0

Consensus-EOM successor:

- pooled successor candidates: 2,027
- recovered @25: 23
- recovered @50: 46
- recovered @100: 88
- recovered @500: 199
- qualified matches: 247
- top-100 dominant precision: 0.7855268477632699
- MRR: 0.022198357894316425
- median top-500 fragmentation: 1.0

2022 gate failures:

- recovered@100 not-lower: **FAIL** (88 < 89)
- top-100 precision not-lower: **FAIL**
- MRR not-lower: **FAIL**

Recovered@50 and fragmentation passed; @25/@500/qualified matches improved but were reporting metrics, not rescue gates.

### 2023

Recurrent-EOM parent:

- recovered @25: 23
- recovered @50: 46
- recovered @100: 89
- recovered @500: 192
- qualified matches: 244
- top-100 dominant precision: 0.7867680236864514
- MRR: 0.0220239288966045
- median top-500 fragmentation: 1.0

Consensus-EOM successor:

- recovered @25: 24
- recovered @50: 45
- recovered @100: 88
- recovered @500: 197
- qualified matches: 252
- top-100 dominant precision: 0.7818269256924375
- MRR: 0.0218250861524136
- median top-500 fragmentation: 1.0

2023 gate failures:

- recovered@50 not-lower: **FAIL** (45 < 46)
- recovered@100 not-lower: **FAIL** (88 < 89)
- top-100 precision not-lower: **FAIL**
- MRR not-lower: **FAIL**

Fragmentation passed; @25/@500/qualified matches improved but were not gates.

## Mechanism check

`mechanism_active=true`.

The successor changed selected nodes/candidate output rather than reproducing the parent, so this is a genuine scientific negative rather than an inactive-method result.

Strict recovered@100 improvement in at least one year: `false`.

## Scientific disposition

Consensus-EOM HDBSCAN v1 is permanently rejected. No strict-vs-nonstrict positivity variant, annual threshold, tie-rule change, scalar/vector blend, ranking change, feature change, HDBSCAN parameter change, or alternate selection rescue is authorized after this binding outcome.

Recurrent-EOM HDBSCAN v1 remains the promoted parent.

Firewall remained clean:

- protected target-region events accessed: false
- OrbitTrace target information accessed: false
- SonotaCo 2013/2014 accessed: false
- EFN accessed: false
- MAARSY scientific access: false
- DMS scientific access: false
