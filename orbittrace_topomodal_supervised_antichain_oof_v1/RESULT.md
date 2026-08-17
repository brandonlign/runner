# OrbitTrace TopoModal supervised antichain OOF v1 — binding result

## Verdict

**FAIL_TOPOMODAL_SUPERVISED_ANTICHAIN_OOF_V1**

This is the first technically valid scientific endpoint under the frozen protocol and is binding. The exact supervised TopoModal antichain OOF v1 mechanism is permanently closed. No feature, target, fold, capacity, target transform, antichain rule, threshold, tie-break, score blend, or ranking rescue is authorized.

The broader practical hypothesis motivating this experiment — that the high-recovery #1284 TopoModal hierarchy merely needed a straightforward rigorously cross-fitted supervised candidate-utility ranker to repair MRR — is not supported by this prospective test and must not be recycled as a v1-style ranking tweak.

## Authoritative provenance

- Branch: `agent/orbittrace-topomodal-supervised-antichain-oof-v1`
- Scientific execution commit: `f38de960a8b8ae023071019f8e89fd17285b93cf`
- Binding workflow run: `32062821745`
- Artifact: `orbittrace-topomodal-supervised-antichain-oof-v1`
- Artifact ID: `9298954965`
- Artifact ZIP SHA-256: `0ec9bad1e6cb4db152e6aca30b7d3e324b158b8494b1c22162ba6f43c8d9baa8`
- Pretruth JSON SHA-256: `22ee242d16e73c553d0e2041e55a8d938963c504a824797e92119d15b4bab7ba`
- Result JSON SHA-256: `92918664bdc57d7645aa068895d8ef312fc01c9c589dc052a0d310d5c7cf76ae`

The two earlier workflow attempts terminated before the pretruth stage because the later branch did not contain the already-frozen support-resolved comparator helper. The only repair was to vendor the exact existing helper Git blob `4988997c023d9df2b504372b4290dcab379a6dcc`. No scientific source, protocol, feature, target, model, selector, or gate changed. Neither earlier attempt opened the supervised scientific endpoint.

## Pretruth audit

The immutable pretruth stage reproduced the authoritative #1284 eligible hierarchy candidate counts exactly:

| scale | bucket 0 | bucket 1 | bucket 2 | bucket 3 |
|---|---:|---:|---:|---:|
| `d=128` | 81 | 98 | 94 | 83 |
| `d=1024` | 9 | 7 | 6 | 9 |

The pretruth seal passed before shower labels were opened.

## Equal-budget results

### Fine scale (`d=1024`)

| metric | recurrent-EOM | supervised TopoModal |
|---|---:|---:|
| qualified total | 20 | **31** |
| mean MRR | **0.6959325397** | 0.5371428571 |
| mean top-100 dominant precision | 0.3530315710 | **0.5886672679** |
| mean median fragmentation | 1.0 | 1.0 |

- qualified nonloss: **8/8** bucket-year panels
- strict qualified wins: **6/8**

### Coarse scale (`d=128`)

| metric | recurrent-EOM | supervised TopoModal |
|---|---:|---:|
| qualified total | 94 | **142** |
| mean MRR | **0.2358453098** | 0.1828145517 |
| mean top-100 dominant precision | 0.3396191654 | **0.5692458747** |
| mean median fragmentation | 1.0 | 1.0 |

- qualified nonloss: **8/8** bucket-year panels
- strict qualified wins: **8/8**
- recovered at 25: 87 vs **126**
- recovered at 50/100/500: 94 vs **142**

Candidate-capacity passed in every panel, so this was not a structural sparsity failure.

## Gates

Eight of ten frozen gates passed. The only failures were again the two MRR gates:

- PASS fine qualified total strictly greater
- PASS fine qualified nonloss >= 6/8
- **FAIL fine mean MRR nonloss**
- PASS fine precision nonloss
- PASS fine fragmentation nonincrease
- PASS coarse qualified total nonloss
- PASS coarse qualified nonloss >= 6/8
- **FAIL coarse mean MRR nonloss**
- PASS coarse precision nonloss
- PASS coarse fragmentation nonincrease

The learned selector therefore preserved the same central TopoModal pattern already seen in support-resolved selection: much stronger recovery and precision, but worse early ordering. It did not repair the MRR blocker. Its MRR was also slightly below the earlier support-resolved result at both scales.

## Interpretation and closure

This result is stronger evidence than historical v29 for this mechanism because it directly tests the actual high-recovery #1284 TopoModal hierarchy with whole-shower nested OOF rather than the older URC/HDBSCAN/Sugar proposal universe.

The failure is specifically ranking/early ordering, not candidate availability: candidate capacity passed everywhere, recovery rose from 20 to 31 at the fine scale and 94 to 142 at the coarse scale, precision rose sharply, and fragmentation did not worsen, yet MRR fell at both scales.

Accordingly:

1. **Do not tune or rescue supervised TopoModal antichain OOF v1.**
2. **Do not recycle the premise that a straightforward candidate-level supervised reranker is the missing fix for the current TopoModal MRR deficit.**
3. No SonotaCo progression is authorized from this experiment because the target-excluded GMN gate failed.
4. Recurrent-EOM / the existing frozen champion remains in force unless a genuinely different preregistered successor passes its gates.
5. Any future mechanism must first be checked against the closed-mechanism ledger and must be scientifically distinct rather than a ranking hyperparameter or feature rescue.

## Firewall / access record

- protected solar longitude `[20.0°,55.0°]`: excluded upstream
- OrbitTrace target information/events: not accessed
- SonotaCo 2013/2014: not accessed
- ASFN/EFN event-level data: not accessed
- AMOS: not accessed
- MAARSY: not accessed
- DMS: not accessed
- post-result parameter search: none
- merge: none
