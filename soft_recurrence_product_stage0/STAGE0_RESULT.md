# Leave-one-year-out recurrence product: authoritative Stage-0 no-go

Runner workflow `30877036663` completed the full frozen benchmark. Artifact `8879926798` was preserved with digest `sha256:549e47acf0eaaff41c544b463c05e8e2d06eddca9680245c526af1ce84109071`.

## Result

For weak recurrent injections with 4 and 6 meteors per active year:

- candidate recurrent recovery: **0.450**;
- candidate one-year-artifact detection: **0.000**;
- candidate recurrence margin: **0.450**;
- strongest baseline recurrent recovery: **0.400**;
- strongest baseline recurrence margin: **0.400**;
- apparent margin gain: **+0.050**.

Candidate ideal-null FWER was **0.000**, but shared-structure-null FWER was **0.240**, above the frozen **0.200** ceiling. The exact floating-point margin comparison also did not clear the predeclared `>= 0.05` gate.

Four of six frozen gates passed. Verdict: **`KILL_SOFT_RECURRENCE_PRODUCT`**.

The statistic successfully rejected one-year artifacts and recovered more weak recurrent injections, but its complete-search threshold did not control the prospectively specified shared-structure null family. No statistic, null mixture, distortion amplitude, threshold, trial count, injection, comparator, or gate will be changed after this result. No known-shower, held-out-year, catalogue, or GhostStream application is authorized.
