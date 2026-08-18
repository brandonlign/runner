# Recurrent-locked local TopoModal trunk v1 — binding result

## Verdict

**FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1 — 15/16 gates passed.**

This is the first technically valid truth result and is binding under the frozen protocol. The exact largest-strict-dominant-mode-trunk lane is permanently closed. No threshold, anchor, radius, depth, precision-proxy, year/rank/size selector, or other result-informed rescue is authorized.

## Provenance

- Scientific branch: `agent/orbittrace-recurrent-local-topomodal-trunk-v1`
- Frozen protocol commit: `7bcd04a2eb8da274499fb7d57ebfa135e6e80ac6`
- Protocol blob: `de8d040a1f9d3b0825ce56532efd5950acefc689`
- Frozen `build_prelabel.py` blob: `cd3fb15263fd4b2e38e4b413ece9b347b64816d5`
- Frozen `evaluate_truth.py` blob: `749a527b7a9ee3c5f1a70832669d83fa1af592d7`
- Execution branch: `agent/orbittrace-recurrent-local-topomodal-trunk-v1-activate`
- Binding execution commit: `d46c52e44e31312cce75480c399ebd85b479b917`
- Binding workflow run: `32099154944`
- Sealed prelabel artifact: `9311157022`, digest `sha256:d938bbd15a5b71051166b0139eea32f280a7d245aac6acea92d3cac517e02781`
- Sealed prelabel SHA-256: `a7b860704c7a688e4dd2a5dd1e38d9a03719b147bc373ee785d446e84a6ff380`
- Binding result/provenance artifact: `9311201208`, digest `sha256:855663c0b485c3882c158e2e63ff71540dd26ea3ad57196b01034877d1d27d95`
- Binding result JSON SHA-256: `e0670b736cdbde0261693bd576f272599200b7656740c524cbac4eb5601f754d`
- Validated constant-memory helper blob: `552f961eddf176ac1789aaf1fc3ff82fdfe627ec`
- Validated technical wrapper blob: `1c45d58db92ba19f8a1f0ad2e138dcfef293d5ea`
- Technical validation run: `32098663887`; rank-1 validation artifact `9310875180`, digest `sha256:e3aec819003d426f9c54e3fce1162fc8934664cc6419e6488955aba562684e04`
- Exact label-free geometry artifact: `9309668009`, digest `sha256:cd16d0cb95f865fc120e506581201e019a6343aba6b6042d0846e05fba119bc0`
- Target-excluded event universe: 738,682 events = 315,024 (2022) + 423,658 (2023), SHA-256 `c97f735e7264918d040ee19a54f3f139c9e8910039d089a5753039bfb247038b`
- Changed catalogue slots: **305 / 2,094**

The lazy-neighbor implementation was a technical storage repair only. Before binding use, the full blocking rank-1 parent completed successfully and ranks 50, 100, and 500 reproduced the frozen implementation exactly in both final membership and serialized topology summary. Frozen science files remained byte-identical. Protected `[20°,55°]` events remained excluded and no SonotaCo, ASFN/EFN event-level, AMOS, MAARSY, or DMS scientific data were accessed.

## Binding metrics

### 2022

| Metric | Parent density-sync Recurrent-EOM | Local TopoModal trunk | Delta |
|---|---:|---:|---:|
| Qualified/recovered showers | 236 | **242** | **+6** |
| Recovered @25 | 22 | **23** | **+1** |
| Recovered @50 | 45 | **47** | **+2** |
| Recovered @100 | 89 | **90** | **+1** |
| Recovered @500 | 192 | **196** | **+4** |
| Zero-filled eligible-query MRR | 0.0147946186 | **0.0150487947** | **+0.0002541761** |
| Historical conditional MRR | 0.0225053732 | 0.0223244516 | -0.0001809215 |
| Mean top-100 dominant precision | 0.7873334043 | **0.7922827253** | **+0.0049493211** |
| Median top-500 fragmentation | 1.0 | 1.0 | 0.0 |

All seven 2022 preservation gates passed.

### 2023

| Metric | Parent density-sync Recurrent-EOM | Local TopoModal trunk | Delta |
|---|---:|---:|---:|
| Qualified/recovered showers | 244 | **247** | **+3** |
| Recovered @25 | 23 | 23 | 0 |
| Recovered @50 | 46 | 46 | 0 |
| Recovered @100 | 90 | 90 | 0 |
| Recovered @500 | 191 | **193** | **+2** |
| Zero-filled eligible-query MRR | 0.0146868566 | **0.0147063261** | **+0.0000194694** |
| Historical conditional MRR | 0.0220302849 | 0.0217915601 | -0.0002387248 |
| Mean top-100 dominant precision | **0.7898245986** | 0.7898042124 | **-0.0000203862** |
| Median top-500 fragmentation | 1.0 | 1.0 | 0.0 |

Six of seven 2023 preservation gates passed. The sole binding failure was `top100_precision_not_lower`: top-100 dominant precision decreased by about `2.04e-5`.

Both global gates passed:

- representation mechanism active: 305 slots changed;
- zero-filled eligible-query MRR strictly improved in at least one year (in fact, both years).

## Scientific interpretation

The experiment strongly supports the underlying representation hypothesis even though the exact frozen rule fails promotion. Holding Recurrent-EOM rank fixed while locally eroding membership increased qualified shower recovery in both years, improved fixed-denominator MRR in both years, improved or preserved every early-recovery gate, and preserved median fragmentation. In 2022 it also materially improved top-100 precision.

The exact rule nevertheless fails because the protocol required **no precision decrease in either year**, and 2023 top-100 precision fell from `0.7898245986` to `0.7898042124`. The size of that miss does not authorize a rescue; the exact lane is closed.

The broader diagnosis is useful for future independently frozen methodology: global reranking is not the only viable lever. Fixed-rank membership representation can improve zero-filled MRR and recovery. A future successor, if any, must use a genuinely distinct pre-frozen representation rationale rather than tuning this trunk depth or adding a selector to repair the single precision miss.
