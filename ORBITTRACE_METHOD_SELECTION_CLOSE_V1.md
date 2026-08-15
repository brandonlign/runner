# OrbitTrace method-selection closure v1

## Status

**Method development is closed.**

The final pre-external-test OrbitTrace method is **density-synchronous recurrent-EOM HDBSCAN v1**, exactly as frozen and executed in PR #1263 at binding head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

This decision is made before any AMOS 2023/2024 event-level scientific access. It does not open AMOS, SonotaCo, EFN, ASFN, MAARSY, DMS, OrbitTrace target information, or protected-target-region events.

The purpose of this record is to stop further result-driven method proliferation on already-exposed GMN development data and to distinguish three different questions that had begun to blur together:

1. which method won its frozen full-GMN development comparison;
2. how robust that development advantage is to perturbation;
3. whether the final frozen method generalizes to the untouched external AMOS survey.

Those are separate questions and remain separate below.

---

## 1. Permanent data roles remain binding

The split frozen in PR #1264 remains unchanged:

- **TRAIN / DEVELOPMENT:** target-excluded GMN 2022+2023.
- **VALIDATION:** SonotaCo 2013+2014, explicitly **EXPOSED DEVELOPMENT ONLY**, for prospectively preregistered future-successor contingencies only.
- **FINAL TEST / external validation:** untouched AMOS 2023+2024, one shot after method selection closes.

The inclusive protected solar-longitude interval `[20°,55°]` remains inaccessible before scientific use.

GMN 2024/2025 is not a fresh holdout. ASFN and EFN are historical diagnostics, not additional selection panels. No new external survey search is authorized.

PR #1263's grandfather rule from #1264 remains binding: #1263 cannot receive a retroactive SonotaCo validation because no such contingency was preregistered before its GMN outcome. If no later method completed the prospective GMN -> SonotaCo challenger path, #1263 could remain the final candidate and proceed to still-sealed AMOS. That is now the situation.

---

## 2. Selected final method: exact #1263 density-synchronous recurrent-EOM

### Scientific definition

The final method retains the pooled GEO6 HDBSCAN hierarchy and all parent HDBSCAN settings, but replaces recurrent-EOM node quality

`R(C) = min(E_2022(C), E_2023(C))`

with the parameter-free density-synchronous local FOSC quality

`S_sync(C) = integral min(A_2022^C(lambda), A_2023^C(lambda)) d lambda`.

The exact identity

`R - S_sync = 1/2 * [ integral |A_2022-A_2023| d lambda - |E_2022-E_2023| ] >= 0`

shows that #1263 is the recurrent-EOM objective minus a nonnegative penalty for year-to-year disagreement in where persistence is accumulated along density lambda. The hierarchy itself is unchanged.

Exact scientific implementation identities remain those already frozen in #1263, including density-synchronous kernel blob:

`587a304f451e41b9503272f1783a6c6ebb295000`

and binding scientific execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

No smoothing, lag/alignment, weighted minimum, parent blend, HDBSCAN modification, reranking, or other post-result variant is authorized.

---

## 3. 🟢 POSITIVE — original binding full-GMN development result remains authoritative

Binding #1263 run:

- run `31852836840`;
- artifact `9238142199`;
- artifact digest `sha256:918992863d019baf3bbb5eadd83ecaa32cabea3d9bd7d9d43735b26474e8ed60`;
- verdict `PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT`.

Versus exact recurrent-EOM v1:

### GMN 2022

- recovered@25 `22 -> 22`;
- recovered@50 `45 -> 45`;
- recovered@100 `89 -> 89`;
- top-100 dominant precision `0.7856486012780942 -> 0.7873334042799703`;
- MRR `0.022498269587309373 -> 0.022505373166085363`;
- fragmentation `1.0 -> 1.0`.

### GMN 2023

- recovered@25 `23 -> 23`;
- recovered@50 `46 -> 46`;
- recovered@100 **`89 -> 90`**;
- top-100 dominant precision **`0.7867680236864514 -> 0.7898245986099988`**;
- MRR **`0.0220239288966045 -> 0.02203028490649908`**;
- fragmentation `1.0 -> 1.0`.

Every preregistered no-regression gate passed and recovered@100 improved strictly in 2023. Candidate count changed only `2,097 -> 2,094`; the top-100 membership overlap was `99/100` and the method acted as the preregistered synchrony penalty rather than a wholesale catalogue rewrite.

This is why #1263 remains the **binding full-GMN development champion**. That statement is not withdrawn by later diagnostics.

---

## 4. 🔴 NEGATIVE robustness diagnostic — the strict recall advantage is sample-sensitive

PR #1265 applied a separately frozen deterministic 10-fold training-perturbation diagnostic to the already-frozen recurrent-EOM and #1263 proposals without refitting a new method or changing candidate order.

Binding aggregate result:

- verdict `FAIL_DENSITY_SYNC_GMN_TRAIN_CV_V1`;
- total recovered@50 across all year-fold panels: `910 -> 910`;
- total recovered@100: **`1761 -> 1761`**;
- mean top-100 dominant precision: **`0.7781536639 -> 0.7786466016`**;
- mean MRR: **`0.02304596725 -> 0.02308159925`**;
- median top-500 fragmentation: `1.0 -> 1.0`;
- mechanism active in `10/10` folds.

The @100 effect is exactly balanced: one fold gives +1 in each year, one fold gives -1 in each year, and the remaining year-fold panels tie, producing aggregate delta zero.

### Binding interpretation

This diagnostic **does not erase #1263's original full-data PASS**, because it asks a different preregistered robustness question. It does, however, prohibit a stronger claim that density-synchronous extraction has demonstrated robust fixed-budget recall superiority on GMN.

The defensible training claim is narrower:

> Density-synchronous recurrent-EOM improved top-ranked purity and reciprocal-rank quality relative to recurrent-EOM in the binding full-data evaluation, while its one-candidate recovered@100 gain was sample-sensitive under the frozen perturbation diagnostic.

The perturbation result is evidence **against more GMN-driven tuning**, not an invitation to find a different fold rule or variant.

---

## 5. 🔴 NEGATIVE direct hierarchy successor — stratified-core is permanently closed

PR #1266 tested one direct architecture-level hypothesis after #1263: require balanced annual local density support with frozen `k_year=5` core radius before applying unchanged density-synchronous extraction.

Binding run `31861760176`, artifact `9240971435`, verdict:

`FAIL_DENSITY_SYNC_STRATIFIED_CORE_V1_GMN_DEVELOPMENT`.

The mechanism was active, but candidate count fell `2,094 -> 1,706`.

### 2022

- @50 `45 -> 44`;
- @100 **`89 -> 81`**;
- precision **`0.7873334043 -> 0.7628887349`**;
- MRR `0.0225053732 -> 0.0229505931`.

### 2023

- @50 `46 -> 44`;
- @100 **`90 -> 78`**;
- precision **`0.7898245986 -> 0.7637124161`**;
- MRR `0.0220302849 -> 0.0231845086`.

The higher MRR cannot rescue the severe fixed-budget recovery and precision regressions. This result supports a coherent methodological interpretation: recurrence is useful as a local **extraction/ranking objective**, but forcing cross-year balance into the density hierarchy itself is too selective for this development corpus.

No alternate `k`, softer/max blend, pooled-core mixture, partial stratification, or reranking rescue is allowed.

---

## 6. Other failed successors remain closed

All previously frozen negative mechanisms remain exactly as recorded in their authoritative PRs/artifacts, including consensus-EOM, cross-year-core, reciprocal-transfer, ECDF recurrent-rank, phase-intensity equalization, RFT, and other closed branches.

Some failures improved one desirable metric while regressing another; that is useful mechanistic evidence, but it is not authorization to combine their successful-looking pieces after viewing outcomes. In particular, the repeated pattern in cross-year-core / reciprocal-transfer / stratified-core is that stronger explicit cross-year structural constraints concentrate some true streams near the top while damaging broader catalogue recovery.

No failed mechanism is reopened by this closure.

---

## 7. Why method search stops here

Continuing to generate successors on the same exposed GMN 2022/2023 endpoint now has decreasing scientific value and increasing selection bias.

The evidence already distinguishes the major design choices:

- recurrence-aware extraction on one pooled hierarchy is viable;
- density-level synchrony provides a clean parameter-free local FOSC objective and passed its original frozen full-GMN gate;
- its fixed-budget recall advantage is small and perturbation-sensitive;
- moving recurrence more aggressively into local density/hierarchy construction has repeatedly hurt breadth of recovery;
- several alternative rank/geometry mechanisms have already produced frozen negative outcomes.

Therefore a new method would increasingly be chosen with knowledge of exactly which exposed GMN metrics prior methods missed. Even if preregistered before its own run, an indefinite sequence of such successors would turn the development corpus into an implicit optimization oracle.

**The scientifically stronger next experiment is external generalization, not another GMN version.**

---

## 8. Final method-selection decision

### Primary final method

**Density-synchronous recurrent-EOM HDBSCAN v1 (#1263), exact frozen implementation.**

### Locked comparators for AMOS

The future one-shot AMOS analysis may include already-frozen comparator methods only to interpret external performance. At minimum these may include:

1. exact recurrent-EOM HDBSCAN v1;
2. exact ordinary HDBSCAN EOM parent under the same representation/settings;
3. already-frozen literature comparator implementations only where the pre-data AMOS contract supplies their required fields and the comparator protocol is fixed before AMOS scientific access.

Comparator results are **not alternative final-method selection opportunities**. If a comparator beats #1263 on AMOS, the project does not switch final methods after seeing the external result.

### Failure rule

If the exact #1263 final method fails its frozen AMOS final-test criterion, the conclusion is:

> external generalization of the selected method was not established by the prespecified AMOS test.

That failure must be published/preserved as such. It does not authorize:

- switching the final method to recurrent-EOM because it happened to look better on AMOS;
- selecting a literature comparator as the new OrbitTrace method;
- modifying #1263;
- rerunning AMOS with a different threshold, metric, rank budget, data subset, year split, or feature mapping;
- opening a new external survey to obtain another chance at a positive result.

---

## 9. Relationship to the old AMOS protocol

PR #1244 froze an AMOS 2023/2024 protocol for **recurrent-EOM v1** before later method development and before any AMOS event-level access. It remains an important historical provenance record and must not be rewritten or deleted.

However, it has never been scientifically executed and no AMOS rows have been opened. Because method selection is now explicitly closed **before AMOS access**, the final selected-method AMOS protocol may supersede #1244 as the one scientific endpoint, provided that the new protocol is itself frozen completely before any AMOS scientific receipt/access and explicitly records this supersession.

The old #1244 endpoint and the new final-selected-method endpoint must **not both be executed sequentially** as separate chances.

The existing staged AMOS acquisition/data-contract work may be reused where it is scientifically unchanged, but no request is sent and no AMOS data are opened by this method-selection closure.

---

## 10. SonotaCo and historical external diagnostics

- SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**. #1263 is not retroactively benchmarked there.
- Recurrent-EOM's exposed SonotaCo superiority remains evidence about recurrent-EOM, not #1263.
- Recurrent-EOM's pristine ASFN negative remains evidence about that exact older method; it is not silently transferred to #1263.
- EFN remains a historical pretruth mechanism-inactive diagnostic with labels sealed.
- None of these panels becomes a new selection chance after this closure.

---

## 11. Paper-level claim discipline

The final paper should not state that #1263 has robustly beaten recurrent-EOM in recall across GMN perturbations. It should distinguish:

- **full-data development:** #1263 passed the frozen superiority gate and improved 2023 recovered@100 `89 -> 90`, with precision/MRR improvements in both years;
- **robustness:** the aggregate perturbation recovered@100 advantage was zero, while mean precision and MRR remained higher;
- **external validation:** unknown until the one-shot AMOS test is completed.

The methodological novelty claim should remain narrow:

> a recurrence-aware local HDBSCAN/FOSC extraction quality that integrates overlap of normalized year-specific persistence mass across density on one pooled hierarchy.

Do not claim first-ever recurrence-aware meteor clustering, and do not conflate development success with external validation.

---

## 12. Firewall at closure

At the time of this decision:

- AMOS 2023/2024 event-level scientific data remain unopened;
- #1263 has not been retroactively run on SonotaCo;
- protected solar longitude `[20°,55°]` remains inaccessible;
- OrbitTrace target information/events remain inaccessible;
- MAARSY and DMS remain scientifically inaccessible;
- no new external dataset is authorized.

This closure authorizes protocol preparation only. It does **not** authorize sending the AMOS data request or opening AMOS scientific data.
