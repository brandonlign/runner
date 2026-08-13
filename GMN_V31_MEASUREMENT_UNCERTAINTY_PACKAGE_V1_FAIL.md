# GMN v31 measurement-uncertainty package v1 — binding failure

🔴 **FAIL — frozen prerequisite did not pass.**

First technically valid package attempt: workflow `31753260669`, job `94623468931`, execution commit `08d07516336c37beb9273681aa95f8d017e441ef`.

The package protocol had been frozen before member-specific raw geometry inspection at commit `532126fb75a66603a765d46353272609196e418c`. It required every immutable P19 hard-family member's raw RA/Dec/Vg point estimate to reproduce the active v31 canonical geometry within `1e-9` in each native coordinate, with no tolerance relaxation or alternate raw-field/transform rescue.

The input/source guards passed and the exact 2022+2023 target-excluded active scan was reconstructed. The first reported frozen-gate mismatch was hard member `20220101021023_TFPnT`: reconstructed Sun-centered ecliptic longitude differed from the active parent value by `0.0004461711147598635` degrees, exceeding the frozen `1e-9` tolerance.

The process stopped immediately. It did not produce `GMN_V31_HARD_MEMBER_MEASUREMENTS.jsonl` or a PASS manifest. No measurement-error candidate ranking, recovery metric, SonotaCo result, target-region result, MAARSY, or DMS result was computed.

Per the frozen protocol, this exact raw-RA/Dec uncertainty-package route is closed. Do **not** rescue it by relaxing the equivalence tolerance, deleting the member, imputing, substituting a different raw coordinate field, changing the J2000 transform, switching years, or otherwise adapting from this mismatch.

The earlier truth-free schema result `PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1` remains valid only as an availability statement: reported marginal uncertainties are essentially complete in the exact v31 event universe. It does not override this package failure.