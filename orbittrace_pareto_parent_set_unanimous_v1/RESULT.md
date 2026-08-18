# OrbitTrace Pareto parent-set unanimous v1 — binding result

## Verdict

**FAIL — 4/5 binding truth gates. Exact lane closed.**

This result is binding. No rescue, thresholding, alternate set order, parent selection, scalar parent summary, or post-result transform is authorized.

## Frozen provenance

- Branch: `agent/orbittrace-pareto-parent-set-unanimous-v1`
- Protocol freeze commit: `a624daab77b64a2870859fab30ab8679a7c49d14`
- Protocol blob: `82b8f9bf19de1322e0c4676f8eadef11b28e3df7`
- Builder blob: `e98cccd91899f19416276a170c5fb683570e54f5`
- Truth evaluator blob: `4c0ce34e2fc57969aeb1ab910f9ec0e7f2f0c21f`
- Activation commit / binding workflow head SHA: `721f4d08f89f1038ea9eb3f2ea021337f2cb3856`
- Binding workflow run: `32105397832`
- Pretruth artifact: `9313005227`
- Pretruth artifact digest: `sha256:0011a6e1e198c89fe83f13785fab5e6909c045789bcb83f551ebc4650df624b2`
- Sealed prelabel SHA256: `18c6a1fddd45aa144e9a0a80e38b8629af7ad08848af99fe189ef715be224b69`
- Truth artifact: `9313063602`
- Truth artifact digest: `sha256:4cdc4bf4832931dcc9601357d4116c3dd981e19d16e5804a0328e3160f0faeee`
- Truth-result SHA256: `9eeeb8f0c89653f3105684204213d488748c0b9a9646b6ceea5e6c77ea7fc9c5`

## Pretruth

All **12/12** frozen structural/firewall gates passed before truth opened.

- exact target-excluded GMN 2022+2023 universe reproduced;
- protected inclusive solar-longitude region `[20°,55°]` remained inaccessible;
- all eight sparse Pareto-prominence orders reproduced exactly;
- full TopoModal memberships were unchanged;
- complete multi-parent rank sets were represented without scalar collapse;
- genuine multi-parent correspondence was active: 12 retained candidates across the four d=64 panels;
- the new set-valued order differed from the frozen barycenter order in every d=64 panel, including top-K.

D=64 panel sizes / equal budgets / multi-parent counts:

- b0: 11,375 events, K=59, multi-parent=3;
- b1: 11,645 events, K=59, multi-parent=3;
- b2: 11,493 events, K=58, multi-parent=4;
- b3: 11,549 events, K=59, multi-parent=2.

## Binding truth result

Aggregate over the frozen eight annual bucket-year panels:

| Metric | Recurrent-EOM | Parent-set unanimous successor |
|---|---:|---:|
| qualified recovery | 153 | **192** |
| recovered @25 | **115** | 104 |
| recovered @50 | 148 | **180** |
| recovered @100 | 153 | **192** |
| recovered @500 | 153 | **192** |
| top-100 dominant precision | 0.3254283130 | **0.4517568392** |
| zero-filled eligible-query MRR | **0.04064735821** | 0.04016973496 |
| historical conditional MRR (diagnostic) | 0.1610735598 | 0.1278004805 |
| reciprocal mass | **24.43809452** | 24.17536770 |
| fragmentation median | 1.0 | 1.0 |

Qualified recovery was nonlower in **7/8** annual panels.

Binding gates:

1. qualified total not lower — PASS;
2. qualified nonlower in at least 6/8 — PASS;
3. zero-filled MRR mean not lower — **FAIL**;
4. precision mean not lower — PASS;
5. fragmentation mean not higher — PASS.

## Scientific interpretation

The set-valued correspondence mechanism successfully fixes the higher-density many-to-many TopoModal↔Recurrent matching problem without scalarizing ambiguous parent matches, and it preserves the successful sparse Pareto relation exactly. It also retains the large recovery and precision gains seen in the barycenter successor.

However, the same fundamental early-rank deficit remains: recovered-at-25 drops from 115 to 104 and total reciprocal mass drops from 24.4381 to 24.1754. Thus the d=64 MRR failure is not primarily caused by how multi-parent correspondence is scalarized. The broader TopoModal replacement ordering is moving too much newly recovered mass ahead of high-value early Recurrent discoveries.

Therefore the exact parent-set unanimous architecture is closed. The next mechanism, if any, must be scientifically distinct from the entire multi-parent correspondence-ordering family rather than another set reduction/order variant.
