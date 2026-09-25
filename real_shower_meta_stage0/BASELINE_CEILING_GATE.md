# Complex-held-out baseline ceiling gate

This gate is frozen before the full five-fold baseline run. GhostStream and the fixed M2026-A1/ESV mask are excluded from all training, validation, and test episodes.

## Purpose

The candidate set model is required to improve mean weak-episode AUROC by at least `0.10` over **every** baseline. Therefore, if any baseline exceeds `0.90`, the fixed gain requirement becomes mathematically impossible because AUROC cannot exceed `1.0`.

This gate tests that implication before spending compute on the neural model.

## Splits

- five deterministic, event-count-balanced folds of complete MDC group/parent holdout units;
- fold `f` is test, fold `(f+1) mod 5` is validation, and the remaining three folds train the solar-longitude model and teacher-label proxy;
- no IAU shower code or related complex occurs in more than one split;
- M2026-A1/ESV-region IAU `-1` events are excluded from every sporadic pool.

## Episodes

- 128 events;
- positive episodes use `k in {4,6,8,12}` real members from one shower-year and real IAU `-1` meteors from the same year and a fixed ±10° solar-longitude window;
- negative episodes contain only real IAU `-1` meteors from the same type of window;
- the primary baseline endpoint uses positives with `k in {4,6,8}` plus all negative episodes;
- two deterministic test replicates are generated for every eligible held-out shower-year-member-count combination.

## Frozen baselines

1. **Solar-longitude-only:** histogram-gradient boosting on absolute episode-center sine/cosine and relative-solar-longitude concentration summaries.
2. **Local density:** maximum neighborhood count in relative solar longitude, Sun-centered ecliptic radiant, and speed. Radius is selected on validation complexes from `{1.0,1.5,2.0,2.5,3.0}` in fixed standardized units.
3. **DBSCAN:** largest cluster size with `min_samples=4`; epsilon is selected on validation complexes from the same fixed grid.
4. **Labeler proxy:** best score against linear radiant/speed drift templates fit only to training-complex showers, using the top eight event similarities.

## Frozen decision

- If the best mean five-fold weak-episode AUROC is greater than `0.90`, verdict is `KILL_REAL_SHOWER_META_GAIN_GATE_MATHEMATICALLY_IMPOSSIBLE`.
- Otherwise, verdict is `PROCEED_TO_COMPLEX_HELDOUT_SET_MODEL`.

The baseline parameters, episode construction, fold assignment, and required `0.10` gain cannot be changed after execution.
