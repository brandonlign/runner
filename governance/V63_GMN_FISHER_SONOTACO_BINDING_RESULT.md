# Binding result — v63 GMN-balanced-Fisher SonotaCo transfer v1

Run: `31566505087`
Job: `94019283967`
Execution head: `99ff584190dddb3446926ba95478a334a6b42881`
Artifact: `9129644254`
Artifact digest: `sha256:82b993b7062c392e87ff874aa7484532db1f69579b0596a6f33b6508346a4a04`

Verdict: `FAIL_V63_GMN_FISHER_ALL_FOUR_LITERATURE_SUPERIORITY_PAIRS`
Panel wins: **1/4**.

All pretruth and parent controls passed before outcome interpretation:
- exact v62 pretruth SHA256: `1988fcb89781a3ba94d19bd7b2e0c058c13b39c73ed020f7931c772952069e64`;
- Sugar 23D feature SHA256: `423c9aef746cd873270cf8950ce79d93620282d12161449ebc99863f748834c7`;
- HDBSCAN 23D feature SHA256: `e0a8162e2b4d73df68552d56f0f81305e28cda1fc539d9e88943e42fb3394663`;
- exact v31 parent orders reproduced all four frozen v31 panel metrics;
- target/protected-data firewall remained intact.

Binding v63 panels:
- Sugar 2013: candidate `0.20791553967041052 / 13`; literature `0.20372657466522806 / 13`; v31 `0.2719801488280529 / 16` — literature pair PASS, materially worse than v31.
- Sugar 2014: candidate `0.21783321644687148 / 12`; literature `0.25901527732153334 / 15`; v31 `0.31529041952487225 / 17` — FAIL.
- HDBSCAN 2013: candidate `0.09407658529080398 / 6`; literature `0.16813025050497152 / 10`; v31 `0.14888037368183737 / 9` — FAIL.
- HDBSCAN 2014: candidate `0.10755516106396801 / 5`; literature `0.15689595582646423 / 9`; v31 `0.15198123772301594 / 9` — FAIL.

Transfer diagnostics:
- auxiliary reference median absolute margin: `2.22299609898299`;
- raw Fisher median absolute score: `6.032787728161278`;
- unit factor: `0.3684857149218033`;
- all-family scaled Fisher SHA256: `f422fbd8f994d653cedee861dbaed52e8ed66cafa924b9ac40cf244bcb9bfca3`.

Scientific conclusion: the target-excluded GMN Fisher success does **not** transfer to the frozen SonotaCo 23D intrinsic representation under the preregistered literal architecture. v63 is permanently rejected. No annual Fisher, local-geometry/Fisher blend, route-specific rule, covariance/prior change, scale change, feature/column change, diversity/fusion change, source quota, membership change, or other post-result rescue is authorized.

v31 remains the strongest demonstrated SonotaCo exposed-development method at 2/4 literature superiority pairs.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation. Protected 20°–55° target information/events, MAARSY, and DMS remained inaccessible.
