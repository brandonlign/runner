# GMN v31 intrinsic ExtraTrees transfer v1

PRE-OUTCOME FREEZE. Development is only the exact target-excluded GMN v31 offline package: 226 families, exact 23D intrinsic X, exact strict groups/folds, and exact qualified-family truth already preserved in that package. No SonotaCo data may be opened unless this GMN gate passes.

Sole ranking change from the reproduced GMN v31-principle parent: replace the k=1 local-geometry margin by strict-OOF positive-class probability from one fixed ExtraTreesClassifier. Capacity is inherited unchanged from the established project classifier: n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809. No scaling, class weighting, resampling, calibration, or model search.

Target is exactly the offline manifest's frozen `truth.positive` qualified-family predicate. Each strict group has total training weight 1: every family receives weight `1 / number_of_families_in_its_strict_group`. The existing deterministic whole-shower five folds are immutable. For each fold fit only on the other four folds and score held-out families by class-1 probability.

OOF probabilities receive the exact inherited diversity order (lambda 0.8, scale 1.0, same centroids/ties), then exact equal 1-based rank-sum with the immutable hard order. No classifier-only order is promotable.

The run must first reproduce exact parent hashes and metrics: @25=23, @50=41, @100=66, precision=0.7229521515453452, MRR=0.050244164168646674, qualified=95. Binding PASS requires @100>66, @25>=23, @50>=41, precision and MRR not below parent, qualified=95. First valid result binds.

If PASS, fit this exact classifier once on all 226 GMN rows with the same weights and freeze it for a separately preregistered label-free SonotaCo portability test. If FAIL, no SonotaCo access and no tree-capacity/weight/target/calibration/feature/fusion rescue.

Protected 20-55, OrbitTrace target information/events, MAARSY and DMS remain inaccessible.