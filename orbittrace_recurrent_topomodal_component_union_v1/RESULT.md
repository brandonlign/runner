# OrbitTrace recurrent-TopoModal component-union v1 — binding result

## Verdict

`FAIL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1`

This is a clean scientific failure of the sole preregistered component-union successor. The exact lane is closed; no membership cap, child omission/selection, alternate union, intersection, threshold, rank change, or post-result rescue is authorized.

## Binding provenance

- frozen protocol commit: `fb7307be9e22acaad0b65d8a596c19964cf28136`
- implementation commits: `65d0f7f85c2a6fc4b8be2443f9bd6afe02f79983`, `a305c1d516b45bd0723a92c15ec59681d59fd718`
- first workflow execution commit: `af4f8061a93b12a6acfa3109aeb6b6222937dcf0`
- first technically valid binding run: `32075895362`
- binding pretruth artifact ID: `9303398748`
- binding pretruth artifact digest: `sha256:7b218cac06e4d1f6fd5811991dcdc5da86edb88437faf8b3d6505c992d92c647`
- binding truth artifact ID: `9303467426`
- binding truth artifact digest: `sha256:73102e5f7963ff0ac4d2423d1fee49c7e5581b11cf09e28e725ebabe33d43b15`
- sealed prelabel SHA-256: `5de736cd67fdbe9ebccd2e3bfbba6a775b50508bf29dfc517f092a1b6ac95453`
- sealed pretruth SHA-256: `068b5fc2b20fefdf23e6251505df506f7f5eeecbc30d71dbbbba25e5af261ea9`
- truth-result SHA-256: `69b566df6f5cecd4351b4e53b3aa435e80ad66977d4cbbcf4d8ef688690c4863`

An execution-registration-only workflow touch later produced run `32076150078`. It is redundant and is not used for scientific interpretation because the protocol binds the first technically valid truth execution.

## Pretruth authorization

The zero-label component construction passed all 12 frozen structural gates before shower truth opened. In particular:

- exactly one successor slot was emitted for every Recurrent-EOM parent;
- parent rank order and equal budget K were preserved exactly;
- every overlap-confirmed TopoModal child was included once in its parent component;
- parent membership was fully contained;
- components were pairwise disjoint and support >=4;
- cross-scale membership stability was nonlower in 4/4 nested bucket pairs;
- aggregate mean-best-Jaccard increased from `0.6183584075451847` to `0.6260160016867004`.

Thus the truth result is interpretable; this is not a structural or execution no-result.

## Binding truth outcome

### Fine sparse scale, d=1024

Recurrent-EOM parent:

- qualified total: **20**
- zero-filled eligible-query MRR mean: **0.3308496315192744**
- historical conditional MRR mean: **0.6959325396825397**
- precision mean: **0.3530315709574533**
- fragmentation mean: **1.0**

Component-union successor:

- qualified total: **20**
- zero-filled eligible-query MRR mean: **0.3244694231859411**
- historical conditional MRR mean: **0.7115575396825397**
- precision mean: **0.35400173664014756**
- fragmentation mean: **1.0**

Panel counts:

- qualified nonlower: **7/8**
- strict qualified wins: **1/8**
- qualified loss panels: **1/8**

Fine gates passed only for panelwise non-regression, precision, and fragmentation. The required strict total-recovery gain and zero-filled MRR non-regression failed.

### Coarse sparse scale, d=128

Recurrent-EOM parent:

- qualified total: **94**
- zero-filled eligible-query MRR mean: **0.06440922700317128**
- historical conditional MRR mean: **0.23584530975502274**
- precision mean: **0.3396191653933494**
- fragmentation mean: **1.0**

Component-union successor:

- qualified total: **92**
- zero-filled eligible-query MRR mean: **0.06411862988507742**
- historical conditional MRR mean: **0.23858460112576735**
- precision mean: **0.3308017086862519**
- fragmentation mean: **1.0**

Panel counts:

- qualified nonlower: **5/8**
- strict qualified wins: **1/8**
- qualified loss panels: **3/8**

Only the fragmentation gate passes at coarse scale.

## Scientific interpretation

The preceding overlap-consensus result showed that full TopoModal modes can isolate additional true showers, but repeated modes from one early Recurrent-EOM parent consume too many equal-budget slots. Component-union tested the opposite extreme: preserve exactly one parent slot and absorb every corroborated mode into that parent's membership.

That does **not** solve the problem. The binding result shows that the TopoModal benefit depends on retaining modal separation. Collapsing those modes back into their broader Recurrent-EOM parent removes the isolation that raised precision/recovery; on coarse panels it even loses two qualified showers and reduces precision. The slight increase in historical conditional MRR while zero-filled MRR falls is also consistent with the already-sealed MRR-definition audit and is not a promotion signal.

The next method, if any, must therefore solve the representation problem without either (a) allowing multiple child modes from one parent to crowd a flat top-K list or (b) merging those modes back into the broad parent membership. It must be a separately motivated and pre-frozen architecture, not a rescue of this union rule.

## Firewall

Throughout the binding run:

- protected solar longitude `[20.0,55.0]` remained excluded;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- ASFN/EFN event-level access was false;
- AMOS, MAARSY, and DMS scientific access was false;
- no post-result alternate component-union search was performed.
