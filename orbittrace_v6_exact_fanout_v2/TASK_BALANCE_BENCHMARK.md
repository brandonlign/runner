# OrbitTrace v6 exact fanout task-balance benchmark

Performance-only benchmark on the immutable target-excluded pre-exact checkpoints from run `31282128101`. No labels, detector outcomes, target-region events, or OrbitTrace information are used.

## Frozen inputs

- 2022 pre-exact artifact: `9028841710`, 66 centers, 143,861 proposals.
- 2023 pre-exact artifact: `9028962091`, 66 centers, 233,980 proposals; checkpoint SHA-256 `c7aec0a9aff3748ed8d02f0070d0567e89df74fc524658c0219b1200d31b4ffa`.
- Work proxy: `proposal_count * window_event_count`. This reflects that immutable `exact_rescore_window_v6` performs full-window geometry work per proposal. The proxy is used only for scheduling; it never enters a detector calculation.
- Six external shards, as in fanout v2.

## 2022

Proposal-count LPT from fanout v2 produced nearly equal proposal loads but estimated work loads:

`[511727857, 331393901, 332866923, 320421387, 317326162, 322292610]`

Worst/best work ratio: `1.612624`.

Center-level work-cost LPT produced:

`[465615735, 333969500, 333912891, 334051600, 333996252, 334482862]`

Worst/best ratio: `1.394423`. The remaining lower bound is the single 260° center.

Task-sliced work-cost LPT splits only centers whose estimated work exceeds one ideal shard. It produced:

`[356049999, 355748269, 355757957, 356246834, 356111792, 356113989]`

Worst/best ratio: `1.001401`. The 260° center is split into two contiguous proposal slices; all other exact proposal semantics remain unchanged.

## 2023

Proposal-count LPT from fanout v2 produced proposal loads of approximately 39k each but estimated work loads:

`[1115901950, 971660965, 727906221, 691482248, 694636246, 647952715]`

Worst/best work ratio: `1.722197`.

Center-level work-cost LPT produced:

`[988860816, 772157973, 772177946, 772056399, 772164899, 772122312]`

Worst/best ratio: `1.280814`. Again, the single 260° center dominates the lower bound.

Task-sliced work-cost LPT splits the 260° center into two contiguous proposal slices and produced:

`[808240856, 808092588, 808290641, 808186225, 808646855, 808083180]`

Worst/best ratio: `1.000698`.

## Integrity boundary

Task slicing is valid only because each proposal is independently passed to the unchanged frozen scalar `exact_rescore_window_v6` with the exact same complete window-event list. `replay_exact_year_tasked.py` requires:

- every shard SHA sidecar;
- exact pre-exact/input hashes;
- complete unique shard indices;
- each task's exact original anchor-ID sequence;
- gap-free, non-overlapping contiguous slices for every center;
- full original proposal order after center reconstruction;
- exact center order when replayed through unchanged `scan_year_v6`;
- unchanged proposal cap 512 and annual primary budget 36,864;
- target-excluded/label-free firewall flags.

No scientific source, proposal, distance, score, component rule, recurrence rule, family rule, ranking, gate, or blind boundary is changed by this scheduler.
