# Frozen result — GMN v31 coordinate-gap concentration diagnostic v1

Protocol commit: `421c621a1581ad2c7f75ae6620dc23849fd687d7`

Authoritative offline package: artifact `9167087908`, digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`.

Exact parent raw OOF margin reproduced at `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Verdict: **PASS_GMN_V31_COORDINATE_GAP_CONCENTRATION_DIAGNOSTIC_V1** (diagnostic only; no new rank or successor evaluated).

Exact parent subsets reproduced before interpretation:

- fused top-100 misses: **29**;
- top-100 misses with no positive-side representative: **25**;
- constituent-absent + sign-rejected top-100 misses: **21**.

For the exact 21 hardest labels, using each label's best exact-v31-margin positive representative:

- negative-contributor count: min **6**, Q1 **7**, median **9**, Q3 **11**, max **13**;
- contributor breadth: **0/21** at <=5 coordinates, **18/21** at 6–11, **3/21** at >=12;
- effective negative-contribution dimension: min **1.4993**, Q1 **3.3141**, median **3.9143**, Q3 **5.0777**, max **6.9883**;
- top-1 negative share: min **0.2284**, Q1 **0.2613**, median **0.3605**, Q3 **0.4679**, max **0.8127**;
- top-3 negative share: min **0.5657**, Q1 **0.6635**, median **0.7867**, Q3 **0.8757**, max **0.9070**;
- top-5 negative share: min **0.7571**, Q1 **0.8507**, median **0.9542**, Q3 **0.9788**, max **0.9997**.

Interpretation: the hard wrong-side geometry is not usually a one-coordinate artifact. Every hard label has at least six coordinates favoring the nearest nonpositive over the nearest positive, with median nine. At the same time, most of the adverse squared-distance mass is carried by several coordinates rather than all 23: the median effective dimension is about 3.9 and the median top-three share is about 78.7%. This supports a multi-coordinate representation-overlap problem, not a single-feature deletion or calibration story.

This diagnostic authorizes no feature deletion, feature weighting, feature subset, clipping, transform, metric change, threshold, or follow-up feature search. Any successor still requires independent motivation and freezing before its first valid outcome.

Protected OrbitTrace target information and the 20–55 degree region remained inaccessible; SonotaCo, MAARSY, DMS, and raw GMN events were not accessed.