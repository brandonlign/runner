# OrbitTrace sporadic member-denoise v1 — frozen GMN development protocol

## Goal
Test one structural, survey-local generalization mechanism on the exact frozen density-synchronous recurrent-EOM winner without recomputing HDBSCAN.

## Fixed parent
- Binding parent run: `31852836840`.
- Binding parent artifact: `9238142199` (`orbittrace-density-synchronous-recurrent-eom-v1-gmn-import-repair-retry`).
- Exact parent successor membership count: **2,094**.
- Exact parent ordered-membership SHA256: `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`.
- Parent GMN recovered@100 total: **179** (2022=89, 2023=90).
- The exact frozen parent memberships/order are inputs. HDBSCAN, its MST, condensed tree, and selected nodes MUST NOT be recomputed in this experiment.

## Fixed survey-background evidence
- Frozen weight run: `31912528972`.
- Frozen weight artifact: `9254119364` (`orbittrace-sporadic-analogue-eom-v1-exact-runtime-retry`).
- `SPORADIC_ANALOGUE_WEIGHTS.npy` SHA256: `648b88efc09192738dcce8eb2af15e215676dd62451a88cd9230337d80fd5347`.
- Each weight is `2*c/(1+c)`, where `c = r_bg/r_actual`; therefore **weight > 1 iff the event is denser than its seasonal-control background**.
- The seasonal controls, k=10, target exclusion, and weight transform are inherited unchanged from the already-frozen sporadic-analogue experiment. No weight recomputation or tuning is authorized here.

## Sole successor mechanism
For each of the exact 2,094 frozen parent families, retain only members whose frozen sporadic-analogue weight is **strictly greater than 1.0**.

- This threshold is not tuned: `1.0` is the identity point of the frozen transform and exactly means local density contrast > 1 versus the seasonal controls.
- If fewer than 10 members remain, drop the family.
- Otherwise keep the family with its surviving membership.
- Preserve the parent family ordering exactly. There is **no reranking**, learned weight, blend, radius, k-search, threshold search, or rescue pass.

This experiment therefore tests member-level denoising, not score reranking.

## Pretruth freeze
Before any hidden known-shower labels are used, persist:
- exact input hashes and run/artifact IDs;
- event-ID to frozen-weight alignment checks;
- exact parent ordered-membership hash;
- successor family count and ordered-membership hash;
- all surviving family memberships in inherited parent order;
- number of removed members/families;
- target/external firewall state.

## Binding GMN success gate
The experiment PASSES only if all conditions hold on target-excluded GMN 2022+2023 development:

1. Total recovered@100 increases from **179 to at least 184** (+5 minimum).
2. For each year independently:
   - recovered@50 is not lower than the frozen parent;
   - recovered@100 is not lower than the frozen parent;
   - top-100 dominant precision is not lower;
   - MRR is not lower;
   - median top-500 fragmentation is not higher.
3. The mechanism is active (at least one membership changes).
4. All reproducibility and firewall checks pass.

Any other scientific outcome is a FAIL. No post-result parameter search, threshold relaxation, blend, rerank, or scientific rescue is authorized for v1.

## Data roles and firewall
- GMN 2022+2023 only, with solar longitude 20°–55° excluded before all method operations.
- Hidden known-shower labels may be opened only after the successor memberships/order are persisted.
- OrbitTrace target information and protected-region events: forbidden.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, DMS: not accessed in this GMN development test.

## Interpretation
A PASS would justify a separately frozen cross-survey transfer test because the mechanism is survey-relative and changes memberships rather than merely exploiting GMN ranking quirks. A FAIL kills this member-denoise mechanism as specified.