# Recurrent-EOM residual-error analysis v1 — result

## 🔴 PhysCore successor not authorized

The frozen residual decomposition on the already-exposed SonotaCo 2013/2014 development panels shows that recurrent-EOM's remaining errors are dominated by ranking/selection and candidate generation, not membership contamination.

Panel-level pooled diagnostic across the four inherited evaluation panels:

- eligible panel-showers: `202`
- recovered under the exact parent Hungarian evaluator: `67`
- residual misses: `135`
- ranking/selection failures: `67 / 135 = 49.63%`
- candidate-generation failures: `58 / 135 = 42.96%`
- membership-contamination failures: `10 / 135 = 7.41%`

Per panel:

| Panel | Recovered | Misses | Ranking/selection | Candidate generation | Membership contamination |
|---|---:|---:|---:|---:|---:|
| Sugar 2013 | 23 | 30 | 14 | 13 | 3 |
| Sugar 2014 | 24 | 26 | 10 | 13 | 3 |
| HDBSCAN 2013 | 11 | 40 | 22 | 16 | 2 |
| HDBSCAN 2014 | 9 | 39 | 21 | 16 | 2 |

The preregistered PhysCore-successor gate required membership contamination in at least two panels **and** at least 15% of pooled residual misses. The first condition passed (`4/4` panels), but the prevalence condition failed (`7.41% < 15%`).

Exact verdict: `DO_NOT_AUTHORIZE_RECURRENT_EOM_PHYSCORE_SUCCESSOR`.

Therefore no recurrent-EOM+PhysCore successor is launched from this diagnostic. The next method work, if authorized separately, should target ranking/selection or missing candidate structure rather than fixed membership cleanup.

This result uses exposed SonotaCo development truth only. Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY, DMS, and pristine external endpoints were not accessed. No post-result parameter search was performed.

Local deterministic result SHA-256 before independent GitHub Actions reproduction: `19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078`.
