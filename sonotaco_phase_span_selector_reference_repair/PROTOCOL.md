# SonotaCo phase-span selector reference-stream repair audit

Status: frozen after PR #125 was invalidated and before any repaired selector score is computed.

## Failure being repaired

PR #125 used reference seed prefix `mondrian-span-selector-reference`, but the frozen selector protocol required the exact PR #112 phase3 reference stream `mondrian-multiview-hires-reference`. The phase3 control therefore failed exact reproduction, invalidating every selector endpoint. This was an implementation mismatch, not a scientific verdict.

## Sole authorized source change

Starting from exact invalid source SHA-256 `aab855db949bd520aa142a51a140c6e181918be0428bdee082b427fd1240a569`, replace exactly one occurrence of:

`mondrian-span-selector-reference`

with:

`mondrian-multiview-hires-reference`

No other source byte, seed, candidate threshold, score, calibration count, test stream, fold, comparator, endpoint, threshold, or gate may change.

## Frozen audit actions

1. Decode the exact original source and require SHA-256 `aab855db949bd520aa142a51a140c6e181918be0428bdee082b427fd1240a569`.
2. Decode the repaired source and require SHA-256 `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`.
3. Compile both sources.
4. Require the textual diff to contain exactly one removed line and one added line, differing only in the reference seed prefix above.
5. Re-run the structural AST checks for thresholds 2.5°/5.0°/7.5°, calibration sizes 128/512/512, conditional original-versus-phase3 selection, complex-held-out selection, and deterministic pseudo-fold assignment.
6. Do not install scientific dependencies, request a mapping artifact, open a meteor archive, construct an episode, or execute a score.

## Decision rule

A pass authorizes only one separately frozen rerun of the unchanged PR #125 selector protocol using the exact repaired source and the exact PR #112 reference stream. Any audit failure kills this repair.

SonotaCo 2024 and GhostStream remain untouched.
