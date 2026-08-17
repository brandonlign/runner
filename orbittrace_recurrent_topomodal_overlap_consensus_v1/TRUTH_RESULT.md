# OrbitTrace recurrent-TopoModal overlap consensus v1 — binding truth result

## NEGATIVE — 9/10 GATES; EXACT ARCHITECTURE CLOSED

Authoritative run: `32072681272`

Execution commit: `dc39def47b65f1c515a2b82b2a0ae80025587f90`

Pretruth artifact: `9302288262`

Pretruth digest: `sha256:a17a0c1e36555953e8f8c986cb3c23e1aded34d0fe6fc28a9a20df374495f9bb`

Truth artifact: `9302423567`

Truth digest: `sha256:c8bf6c724301f6fea2d0d80f458314a5de24581b8313b5f93714585db05c0ea3`

Immutable successor prelabel SHA-256: `bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f`

Pretruth result SHA-256: `b9a9979905b4af1b14441b31f402b6b449d4b5434736feb2e1a8004df326f5ca`

Exact verdict:

`FAIL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1`

The two-stage endpoint completed its frozen scientific contract. The pretruth stage passed all 12 zero-label gates before labels were opened. The truth stage used the preregistered zero-filled eligible-query MRR gate established before this successor outcome; historical conditional MRR remained diagnostic only.

## Fine sparse scale (`d=1024`) — all five gates PASS

| aggregate | Recurrent-EOM | overlap consensus |
|---|---:|---:|
| qualified matches | 20 | **30** |
| recovered@25 | 20 | **30** |
| precision mean | 0.3530315710 | **0.5809589346** |
| zero-filled MRR mean | 0.3308496315 | **0.3980024093** |
| pooled zero-filled MRR | 0.2873376623 | **0.3566829004** |
| historical conditional MRR | **0.6959325397** | 0.5480307540 |
| fragmentation mean | 1.0 | 1.0 |

Qualified recovery: `8/8` nonlower, `6/8` strict wins, `0/8` losses.

## Coarse sparse scale (`d=128`) — four of five gates PASS

| aggregate | Recurrent-EOM | overlap consensus |
|---|---:|---:|
| qualified matches | 94 | **106** |
| recovered@25 | **87** | 71 |
| precision mean | 0.3396191654 | **0.5052656656** |
| zero-filled MRR mean | **0.0644092270** | 0.0545240300 |
| pooled zero-filled MRR | **0.0632519005** | 0.0536378335 |
| historical conditional MRR | **0.2358453098** | 0.1764787519 |
| fragmentation mean | 1.0 | 1.0 |

Qualified recovery: `7/8` nonlower, `5/8` strict wins, `1/8` loss.

The sole frozen gate failure is:

- `coarse_zero_filled_mrr_mean_not_lower`.

All fine gates and all other coarse recovery/precision/fragmentation gates pass.

## Zero-label structural interpretation

The sealed pretruth catalogue was structurally strong: successor cross-scale mean-best-Jaccard `0.7445396005` versus Recurrent-EOM `0.6183584075`, nonlower in all `4/4` nested bucket pairs.

However, the lexicographic parent-block ordering lets multiple full TopoModal modes from an early Recurrent-EOM parent consume multiple equal-budget slots. At coarse scale the first K successor rows cover only 8–17 distinct Recurrent parent families while `K=29–38`. This provides a label-free structural explanation for why aggregate recovery and purity can improve while early reciprocal-rank mass still regresses at coarse scale.

## Binding closure

This exact overlap-confirmed full-TopoModal catalogue and parent-block ordering is permanently closed. Do not rescue it by round-robin/interleaving, selecting one child per parent, source quotas, changing overlap to Jaccard/F1/containment, adding centroid thresholds, admitting zero-overlap support candidates, merging only selected children, changing K, or changing the frozen metric contract after outcome.

A later successor must be a genuinely different candidate architecture, not a rerank of these retained rows.

Protected solar longitude `[20°,55°]` remained excluded. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS were not accessed.
