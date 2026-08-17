# Phase-neutral density-synchronous recurrent-EOM v1 — binding GMN result

## Verdict

`FAIL_PHASE_NEUTRAL_DENSITY_SYNC_V1_GMN_DEVELOPMENT`

The pre-specified GEO4 phase-neutral successor does **not** replace the frozen GEO6 champion. This closes the exact v1 hypothesis. No phase-weight rescue, geometry interpolation, HDBSCAN retuning, rank fusion, or other post-result tuning is authorized by this protocol.

## Binding provenance

- Paired scientific run: `32030877032`
- Execution commit: `86a7d7cffbc07da966e8a24a81df2c628fb1b824`
- Result artifact: `9288955068` (`orbittrace-phase-neutral-density-sync-paired-gmn-repair-retry-v1`)
- Artifact digest: `sha256:de4d489700506d6111c51114819386279db20057df46628837fd1d5c772b39f3`
- Binding result SHA-256: `dcfe3b6b09eb5b2e71ef8f243e897c1a731b2592b276eb0fc9f8591c73dfeab7`
- Pretruth SHA-256: `da790cd186eb4bf208ff4bb08fdc00cc42077a293b30919e7f3ec46a0e12a918`
- Immutable snapshot: run `31996666561`; 315,024 events in 2022 and 423,658 in 2023; 738,682 total.
- Protected solar-longitude interval `[20°,55°]` remained excluded.
- GEO6 and GEO4 were both fully built before sealed truth was downloaded.
- The loader compatibility repair was separately audited on synthetic rows only in run `32030538275` (14/14 checks PASS) before the scientific retry.

## Pretruth structure

| Method | Representation | Candidate count |
|---|---|---:|
| frozen champion | GEO6 | 2,094 |
| frozen successor | GEO4 phase-neutral | 2,620 |

The intended mechanism was active: removing solar phase materially changed the hierarchy and increased the candidate universe by 25.1%.

## Binding metrics

### 2022

| Metric | GEO6 | GEO4 | Successor change |
|---|---:|---:|---:|
| recovered@25 | 22 | 20 | -2 |
| recovered@50 | 45 | 34 | -24.4% |
| recovered@100 | 89 | 36 | -59.6% |
| recovered@500 | 192 | 53 | -72.4% |
| top-100 dominant precision | 0.7873 | 0.3983 | -49.4% |
| MRR | 0.02251 | 0.04925 | +118.8% |
| median top-500 fragmentation | 1.0 | 1.0 | unchanged |
| qualified matches | 236 | 81 | -65.7% |

### 2023

| Metric | GEO6 | GEO4 | Successor change |
|---|---:|---:|---:|
| recovered@25 | 23 | 21 | -2 |
| recovered@50 | 46 | 35 | -23.9% |
| recovered@100 | 90 | 42 | -53.3% |
| recovered@500 | 191 | 53 | -72.3% |
| top-100 dominant precision | 0.7898 | 0.4022 | -49.1% |
| MRR | 0.02203 | 0.05178 | +135.0% |
| median top-500 fragmentation | 1.0 | 1.0 | unchanged |
| qualified matches | 244 | 79 | -67.6% |

GEO4 failed the recovered@50, recovered@100, and top-100 precision non-inferiority gates in **both** years. It passed only the MRR and fragmentation non-inferiority gates. `strict_recovered_at_100_improvement_some_year = false`.

## Scientific interpretation

The result strongly falsifies the simple mechanism that solar phase is globally harmful because it over-separates recurrent radiant-speed structure. Solar phase is instead carrying essential *candidate-generation/disambiguation* information: removing it creates more hierarchy candidates, but the number of qualified shower matches collapses by roughly two thirds and top-100 precision is cut roughly in half in both years.

At the same time, the surviving GEO4 matches are systematically earlier-ranked: MRR more than doubles in both years despite the severe coverage loss. That split is reproducible across both years and suggests that **candidate construction and candidate ordering should not be treated as the same geometry problem**. The next scientifically defensible lane is therefore not a partial solar-phase weight chosen from these labels. It is to keep the successful GEO6 hierarchy frozen and investigate a label-free ordering/selection mechanism on those existing candidates, consistent with the earlier residual analysis showing ranking/selection as the largest single residual failure class.

## Governance consequence

- Exact phase-neutral GEO4 v1 is closed.
- The dormant SonotaCo contingency is **not authorized**, because the GMN promotion gate failed.
- GEO6 remains the density-synchronous geometry champion for this line of development.
- No protected target-region, AMOS, MAARSY, DMS, or pristine external data were used.
