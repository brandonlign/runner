# OrbitTrace label-free v6 — terminal SAAMER external-evidence synthesis

## Scope

Artifact-only synthesis frozen after completion of the two preregistered SAAMER external panels. This synthesis may not download or parse any meteor catalogue, access OrbitTrace target information, rerank a family, alter a gate, pool the two panels into a new pass statistic, or retroactively redefine either panel's verdict.

## Immutable inputs

### SAAMER 2020–2021
- run `31210007928`;
- artifact `9006709213`;
- artifact ZIP SHA-256 `e96e736b4e1d541fb4334d57bf20692404920e616857b783c88d1acba17a77f0`;
- frozen verdict `INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER`.

### SAAMER 2022–2023
- run `31212256679`;
- artifact `9007437717`;
- artifact ZIP SHA-256 `0e4482d750d8dea93ef56205180b4d456aaedc4adb6dc04d9239a35ab32cab50`;
- frozen verdict `INCONCLUSIVE_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_POWER`.

## Questions

1. Did either panel fail a non-power integrity gate?
2. Did either panel reach the preregistered family-universe power minimum `N>=100`?
3. Did either panel reach the preregistered orbitally corroborated-family minimum `Q>=30`?
4. Was the registered ranking endpoint nondegenerate (`K=min(100,N) < N`) on either panel?
5. Is a powered external superiority claim supported?
6. Does the preregistered continuation rule authorize OrbitTrace target reveal?

## Frozen interpretation rules

- Preserve each panel's original verdict exactly.
- No pooled family universe, pooled hypergeometric test, meta-analysis pass threshold, combined rank, or combined p-value is permitted because none was preregistered.
- If both panels are integrity-clean but `N<100`, classify the external programme as **power-limited** rather than scientific failure.
- If `K=N`, explicitly record that top-K corroborated counts cannot distinguish rankings because every family is included.
- A panel's descriptive median ranks/MRR may be reported but cannot substitute for the preregistered endpoint.
- `authorizes_target_reveal` is true only if at least one original external artifact has its original powered-pass verdict. No synthesis can create authorization.

## Terminal verdicts

- `TERMINAL_EXTERNAL_VALIDATION_POWERED_PASS` only if an input artifact already has a powered external PASS verdict.
- `TERMINAL_EXTERNAL_VALIDATION_SCIENTIFIC_FAIL` only if an input artifact has a powered scientific FAIL verdict and none has a powered PASS.
- `TERMINAL_EXTERNAL_VALIDATION_INCONCLUSIVE_POWER_LIMITED` if all completed panels are integrity-clean but none achieves a powered pass/fail because the preregistered power conditions are unmet.
- `TERMINAL_EXTERNAL_VALIDATION_INTEGRITY_FAILURE` if an input panel has a binding non-power integrity failure.

## Claim boundary

A power-limited terminal result supports only:

- label-free v6 passed target-excluded GMN development;
- two independent SAAMER year-pair executions completed under frozen, label-free, target-blinded pipelines;
- the external ranking-superiority endpoint was not statistically identified under the preregistered family-universe requirements.

It does **not** support robust external validation, external superiority, a best-method claim, or opening the OrbitTrace target region under the existing preregistration.
