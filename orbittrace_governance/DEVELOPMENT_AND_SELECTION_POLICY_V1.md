# OrbitTrace development and final-candidate policy — v1

## Purpose

Make method development aggressive without consuming the permanent test panel. The objective remains a target-free meteor-stream discovery method that can beat the strongest relevant literature methods, generalize without retuning, and only then enter the blind OrbitTrace search.

## Development evidence

The only method-selection corpus is target-excluded GMN 2022/2023.

A successor may be designed after a scientific failure, but it must attack a diagnosed mechanism rather than merely alter a nearby threshold. Previously exposed literature-test results may motivate broad architectural questions, but their numerical outcomes cannot choose a new parameter, threshold, feature weight, rank cutoff, or membership boundary.

## Internal development standard

A candidate considered for eventual final-test promotion must demonstrate all of the following on GMN 2022/2023 before the permanent SonotaCo test is opened:

1. **Sparse-stream gain:** material improvement in weak/sparse known-shower recovery, including the 4–9-member regime, not only aggregate F1.
2. **Overall non-regression:** no material loss in qualified-family count, ranking recovery, and dominant-family precision relative to the strongest surviving development baseline.
3. **Year robustness:** the claimed gain must appear independently in both development years rather than being driven by one year.
4. **Stress robustness:** the gain must survive fixed internal perturbations/ablations appropriate to the architecture, such as leave-window-out, support thinning, bootstrap/resampling, or deterministic subpanel checks, without changing the scientific rule after seeing those stress outcomes.
5. **Mechanistic plausibility:** the architecture must have a clear reason to improve the failure mode it targets. Tiny post-failure threshold edits do not qualify as a new architecture.
6. **Target independence:** no OrbitTrace target information or target-region result may enter development.

Development gates can be stricter for a particular successor when frozen before execution. They may not be weakened after a result is observed.

## Architecture triage

Scientific failures are used to kill architectures quickly.

- P18 is a permanent matched-literature no-go.
- B1 is a permanent development no-go.
- No P18 or B1 threshold/feature/model rescue is allowed from their observed results.
- P19 is the current active successor and remains scientifically frozen; this policy does not modify its source, rule, or gates.
- If P19 fails scientifically, the next successor returns to the same GMN 2022/2023 corpus. It does not receive a new SonotaCo year.

A successor after P19 should be materially different if P19's diagnosed structural hypothesis fails. Repeated nearby variants of a rejected mechanism should not be treated as independent progress.

## Final-candidate declaration

Passing one development experiment does not automatically consume the permanent SonotaCo test.

The permanent SonotaCo 2013/2014 test is opened only when the project explicitly declares a candidate **FINAL_FOR_LITERATURE_TEST**. Before that declaration:

- scientific source is frozen;
- all method parameters are frozen;
- complete candidate-generation, family-construction, membership, ranking, and output semantics are frozen;
- Sugar and catalogue-HDBSCAN interfaces are frozen;
- pairwise matched-universe construction is frozen;
- superiority and integrity gates are frozen;
- the target firewall is source-audited;
- no SonotaCo 2013/2014 scientific value has been inspected.

This declaration is intentionally expensive. It should occur only after the method is strong enough on GMN that we are willing to accept the one-shot test result without retuning.

## Test consequence

The SonotaCo 2013/2014 result is final evidence for the declared candidate. If it fails, that exact candidate does not have a literature-superiority claim. The result may not be used to retune the same candidate and then claim a fresh pass on the same panel.

The permanent split is designed to delay this event until development is mature, not to create an endless supply of test panels.

## External consequence

Only a literature-test pass can activate MAARSY 2020/2021. MAARSY remains no-retuning validation, not development data.

Only satisfaction of the external-generalization requirement can activate the final blind OrbitTrace search.
