# OrbitTrace joint density + trajectory conformal expansion v5 — final frozen development protocol

## Purpose

This is the final mechanistically justified post-discovery membership successor in the current v8 development chain.

The preceding one-shot target-excluded experiments established complementary facts on the exact same promoted-v8 226-family universe:

- v3 family-density conformal membership sharply reduced contamination, restored top-100 precision above the frozen 0.65 gate, and improved macro F1, but under-completed membership and missed the required +0.10 annual mean-F1 gain in both years;
- v4 cross-year affine-trajectory conformal membership crossed the +0.10 annual mean-F1 gate in both years and improved large-shower coverage, but overexpanded and lost the precision/qualified-match gates.

v5 therefore tests exactly one architecture: combine v3's local seed-density conformity and v4's cross-year trajectory conformity into a single equal-weight empirical joint nonconformity, then recalibrate that combined score against the source family's own original seed events. No weight, alpha, radius, model, or combination-family search is permitted.

If v5 fails, this post-discovery membership-development chain closes. No Fisher weight, alpha, hard ceiling, activity padding, neighbor order, model order, or alternative p-value combiner may be tuned from the result.

## Frozen base and immutable prerequisites

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Reproduce exactly 226 v8 recurrent families, pooled-year centroids, 128-event scores, multiplicity order, and passed-v8 pre-expansion metrics before membership expansion.
- v3 immutable no-go: run `31235705928`, artifact `9015557724`, digest `sha256:f702124b40452624ffc7210e52978e6d9622e60f0a000af3299abda81e3fa7d7`.
- v4 immutable no-go: run `31236717050`, artifact `9015902170`, digest `sha256:394a03e4ba9ef2013adb4e22e3708f7d330fdd80b4ab603a102829afda50287c`.
- Both exact predecessor artifacts and source implementations must be verified before v5 scientific-value access.
- v8 proposal generation, components, connected family graph, original seed membership, pooled centroids, scores, multiplicity ranking, and family IDs remain unchanged.

## Frozen source evidence channels

For each family and target year independently, use only the family's **original v8 seed events from the other year**. Require at least four source seeds.

### Channel D: family-density conformity

Reuse exactly the v3 geometry:

1. for every source seed, compute its leave-one-out second-nearest-source-seed distance `d2_i` in the exact inherited v8 metric;
2. for a target event, compute nearest and second-nearest other-year source-seed distances `d1_t`, `d2_t`;
3. retain the inherited necessary hard ceiling `d2_t <= 1.5`.

### Channel T: trajectory conformity

Reuse exactly the v4 geometry:

1. fit fixed order-1 ordinary-least-squares functions for Sun-centered longitude, ecliptic latitude, and geocentric speed versus solar longitude using all original other-year source seeds;
2. calculate source leave-one-out trajectory residuals `r_i` by refitting after withholding each source seed;
3. restrict target events to the source family's minimum circular solar-longitude activity arc padded by the inherited `6°` on both sides;
4. calculate target trajectory residual `r_t` with the exact v4 residual metric;
5. retain the inherited necessary hard ceiling `r_t <= 1.5`.

No source shower label, family rank, score, orbital element, or target-year event is used to fit either source channel.

## Frozen joint empirical conformal rule

The marginal conformity ranks are computed from the source reference values without any fitted weight.

For each source seed `i` among `n` source seeds:

- `pD_i = #{j: d2_j >= d2_i} / n`;
- `pT_i = #{j: r_j >= r_i} / n`.

The source joint nonconformity is the equal-weight Fisher form

`S_i = -2 * (log(pD_i) + log(pT_i))`.

For a target event:

- `pD_t = (1 + #{j: d2_j >= d2_t}) / (n + 1)`;
- `pT_t = (1 + #{j: r_j >= r_t}) / (n + 1)`;
- `S_t = -2 * (log(pD_t) + log(pT_t))`.

No chi-square reference distribution is used. The combined statistic is itself empirically recalibrated against the source seeds:

`pJoint_t = (1 + #{i: S_i >= S_t}) / (n + 1)`.

A family-event pair is eligible only when all of the following fixed conditions hold:

1. target event is inside the inherited source activity arc +/−6°;
2. `d2_t <= 1.5`;
3. `r_t <= 1.5`;
4. `pJoint_t > 0.05`.

There is **no separate marginal p-value cutoff**. Density and trajectory evidence enter only through the equal-weight Fisher statistic plus their inherited hard-coherence ceilings.

If an event is eligible for multiple families, assign it exclusively to the family with the largest `pJoint_t`; ties use smaller `S_t`, then stable family ID. Newly assigned events never become source support, and original v8 seeds are never removed.

## Why this is one justified candidate rather than a search

The two channels were selected before v5 because v3 and v4 separately demonstrated complementary mechanisms under immutable no-go records. Equal-weight Fisher combination introduces no fitted coefficient. Empirical recalibration avoids assuming independence between density and trajectory evidence. Every numerical constant is inherited unchanged from v3/v4 or is the conventional conformal `0.05` level already used by both predecessors.

No alternate combiner (Tippett, Stouffer, product without recalibration, conjunction, minimum p, rank sum), weighting, alpha, neighbor order, trajectory model, activity padding, residual ceiling, or density ceiling is evaluated.

## Development panel, blindness, and method-shopping boundary

- Exact target-excluded GMN 2022 + 2023 development corpus inherited from v8.
- Solar longitude 20°–55° is removed before proposals, labels, scoring, expansion, or evaluation by the frozen parser.
- Exact v8 ranking and the complete v5 expanded-membership payload are SHA-256 frozen before known-shower labels are evaluated.
- No OrbitTrace coordinate, identity, member, target-region event, Stage A/B output, or reveal may be accessed.
- The already-seen SonotaCo literature benchmark is not used to choose any v5 constant or combiner.
- Because v1–v4 have already exposed this development panel, a v5 development pass is **not sufficient for promotion to a final method or superiority claim**. A pass authorizes only one separately frozen prospective validation on genuinely fresh data. The literature comparison and OrbitTrace application remain prohibited until that validation passes.

## Scientific gates

Reuse the exact v1–v4 promotion standard without relaxation:

1. multiplicity recovery@100 after expansion `>= 58`;
2. qualified matches after expansion `>= 95`;
3. top-100 dominant precision after expansion `>= 0.65`;
4. expanded macro F1 `>= v8 macro F1 + 0.05`;
5. all-shower annual mean-F1 gain `>= +0.10` in both 2022 and 2023;
6. 4–9 annual mean-F1 delta `>= -0.02` in both years;
7. at least one moderate/large bin (`10–24`, `25–49`, `50–99`, `100+`) has mean-F1 gain `>= +0.10` in both years.

All exact-v8 reproduction, exact v3 density geometry, exact v4 trajectory geometry, other-year-only support, equal-weight Fisher formula, empirical joint recalibration, alpha=0.05, inherited hard ceilings, inherited activity padding, no-recursion, exclusive-assignment, exact-128-episode, Brown-equivalence, pre-label-hash, and target-exclusion integrity gates must pass.

## Decision rule

- **Pass:** every integrity and scientific gate passes. Freeze v5 as a development candidate and immediately stop development; authorize only a separately preregistered fresh prospective validation.
- **Fail:** preserve v5 as a permanent no-go and close this membership-development chain. Do not tune the joint rule from the result.

Neither outcome authorizes OrbitTrace reveal by itself.
