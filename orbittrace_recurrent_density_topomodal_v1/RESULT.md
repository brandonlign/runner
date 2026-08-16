# Recurrent-density topomodal v1 — binding result

## Verdict

🔴 **FAIL_RECURRENT_DENSITY_TOPOMODAL_V1 — CLOSED.**

Binding workflow run: `31964690631`

Binding workflow job: `95207931258`

Binding artifact: `9268217002` (`orbittrace-recurrent-density-topomodal-v1`)

Binding artifact ZIP digest:

`sha256:9232e7df47a28f26f38b68f7edc5a251d25c40635f22dcd9814a28ec250f7367`

Immutable prelabel SHA-256:

`441c65a222807eaa187a45832a5b51a80e64397567ff4963420c5baa454df07c`

The recurrent-density field, complete ToMATo hierarchy, deterministic ranking, recurrent-EOM comparator memberships, source hashes, and firewall state were sealed before shower truth was evaluated. The result below is the first technically valid outcome and is binding.

## Frozen method

The only scientific change from the fixed-scale #1284 topomodal hierarchy was the pointwise ToMATo density field on the unchanged exact radius-1 physical graph:

`rho_22(i) = d_22(i) / N_22`

`rho_23(i) = d_23(i) / N_23`

`rho_rec(i) = min(rho_22(i), rho_23(i))`

No pseudocount, smoothing, floor, power, alternate annual combiner, event deletion, radius change, support-k core distance, or post-hoc rank fusion was used. The complete leaf/internal/root hierarchy and the native #1284 ranking semantics were then applied to `rho_rec`.

## Aggregate truth result

### Fine sparse scale — denominator 1024 (~0.7k pooled events per subset)

| Metric | recurrent-EOM | recurrent-density topomodal |
|---|---:|---:|
| qualified total | 20 | **31** |
| recovered @25 | 20 | **31** |
| recovered @50 | 20 | **31** |
| recovered @100 | 20 | **31** |
| recovered @500 | 20 | **31** |
| mean dominant precision | 0.3530315709574533 | **0.5964797679172679** |
| mean MRR | **0.6959325396825397** | 0.5354687499999999 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: 8/8 nonlower, 6/8 strict wins, 0 losses.

### Coarse sparse scale — denominator 128 (~5.8k pooled events per subset)

| Metric | recurrent-EOM | recurrent-density topomodal |
|---|---:|---:|
| qualified total | 94 | **121** |
| recovered @25 | 87 | **118** |
| recovered @50 | 94 | **121** |
| recovered @100 | 94 | **121** |
| recovered @500 | 94 | **121** |
| mean dominant precision | 0.3396191653933494 | **0.5079353059542803** |
| mean MRR | **0.23584530975502274** | 0.21045688309900057 |
| mean fragmentation | 1.0 | 1.0 |

Panelwise qualified recovery: 8/8 nonlower, 6/8 strict wins, 0 losses.

## Frozen gates

Passed 8/10:

- fine qualified total strictly greater;
- fine qualified nonlower in >=6/8 panels;
- fine top-100 dominant precision not lower;
- fine fragmentation not higher;
- coarse qualified total not lower;
- coarse qualified nonlower in >=6/8 panels;
- coarse top-100 dominant precision not lower;
- coarse fragmentation not higher.

Failed:

- **fine mean MRR not lower**;
- **coarse mean MRR not lower**.

The preregistered verdict requires all ten gates, so this exact architecture fails.

## Recurrent-density sparsification diagnostic

The immutable prelabel shows that the strict pointwise annual minimum makes most sparse-panel events zero-density:

### d=128

- bucket 0: 1,848 positive / 3,719 zero;
- bucket 1: 1,883 positive / 3,957 zero;
- bucket 2: 1,893 positive / 3,964 zero;
- bucket 3: 1,801 positive / 4,015 zero.

### d=1024

- bucket 0: 130 positive / 547 zero;
- bucket 1: 143 positive / 596 zero;
- bucket 2: 135 positive / 601 zero;
- bucket 3: 161 positive / 605 zero.

Thus roughly two-thirds to four-fifths of events receive zero recurrent local density under severe thinning. The architecture nevertheless preserves a strong candidate-recovery and purity advantage, but the annual-minimum field does not prioritize those stream candidates early enough.

## Scientific interpretation

This result is informative beyond another ranking miss:

1. The fixed-radius topomodal family continues to beat recurrent-EOM strongly on sparse **candidate coverage and purity**.
2. Moving recurrence upstream into a simple pointwise repeated-observation density does **not** solve the MRR bottleneck.
3. At d=128, recurrent density trades some of pooled #1284's recovery (about 121 qualified here versus about 140 in the pooled-density hierarchy) for a modest MRR improvement (about 0.210 here versus about 0.187 in pooled #1284), but it still remains below recurrent-EOM's 0.236.
4. At d=1024, MRR remains essentially in the same failed range as pooled #1284 while the strict annual minimum zeroes most events.
5. Therefore a single scalar obtained by pointwise minimum of annual local densities is not the right way to encode recurrence for this problem.

This closes the exact `min(rho_22,rho_23)` density architecture. Do **not** rescue it by testing harmonic/geometric/arithmetic means, pseudocounts, epsilons, clipping, smoothing, alternative annual weights, or result-informed density transforms.

The next successor should change the candidate topology itself so that the two annual density fields can remain distinct rather than being collapsed to one scalar before hierarchy construction.

## Conditional SonotaCo transfer

The pre-frozen exposed SonotaCo transfer protocol was **not executed** because the GMN promotion gate failed. SonotaCo 2013/2014 remains exposed development only.

## Firewall

The inclusive protected solar-longitude interval `[20°,55°]` remained excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, AMOS scientific data, MAARSY, or DMS entered the GMN experiment.