# Frozen result — GMN v31 F-parameter recurrence v1

Verdict: **TECHNICAL_NO_GO_GMN_V31_FPARAM_KS_V1_BEFORE_SCORE**

Frozen protocol commit: `29e27349002160720daed6069621a8ce83021fa4`  
Initial implementation commit: `ec0f091a16cc090a78e0ecdf812799ec46b2daf7`  
Implementation-only member-scope repair: `aff203f32fac7961f2cd8f48f4a23247851516da`

## Execution history

### Run 31706280894 — engineering no-result

The original implementation validated the preregistered F-domain requirement on all blind-allowed GMN events rather than only the exact frozen family members. It failed on non-family event `20220104014226_9I1Ui` with `f_param=1.09`. No candidate score was produced. The scientific protocol was unchanged; only the validation scope was repaired to the exact frozen member universe specified by the protocol.

### Run 31706794198 — engineering no-result

The compact repaired workflow omitted the frozen catalogue-runtime decode/audit step and failed before GMN science with a missing runtime module. No scientific source execution or candidate score occurred.

### Run 31706956388 — binding feasibility result

Job: `94469808833`  
Execution head: `68e7731dbd1ef7a194f4d1286d2a4e7e1f06a5e1`  
Provenance artifact: `9183682357`  
Artifact digest: `sha256:c4707beaf902994eea2f6f6a4a3718aaee079feafbb3616654134b3b29320f87`

This run passed the frozen source/runtime audit and all immutable ranker/V8/P19/offline-package checks, reconstructed the target-excluded GMN 2022+2023 universe, and entered the sole frozen F-parameter feasibility/candidate step.

It then encountered an **actual exact frozen-family member**:

- event ID: `20220801004511_r3Lub`
- official parsed `f_param`: **-0.193**

The frozen protocol requires every retained exact-member F value to be finite and in `[0,1]`; any actual retained member outside that interval makes the exact method a technical no-go, with no imputation or relaxed domain.

Therefore the method terminates **before any 24D candidate margin, rank, or GMN metrics exist**. There is no scientific PASS/FAIL score to interpret and no SonotaCo authorization.

## Closure

Do not rescue this lane by:

- relaxing or expanding the `[0,1]` domain;
- clipping F values;
- dropping out-of-range exact members;
- changing the missing-value rule or family-year minimum;
- recomputing F from begin/peak/end heights;
- substituting begin/end/peak height, duration, magnitude, mass, deceleration, fragmentation, KB/PE/AL, or another light-curve/ablation feature;
- changing the F statistic, transform, threshold, weight, metric, k, scaling, diversity, or fusion;
- blending with the closed activity-profile-KS successor.

The F/light-curve lane is closed from this outcome.

## Firewall

Protected solar longitude 20°–55° remained excluded before any retained F value. No OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, or DMS was accessed. No candidate result exists.