# Annual-density bifiltration GMN ranking v1 — binding result

## Verdict

🔴 **FAIL_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY — CLOSED.**

Binding workflow run: `32078149349`

Binding execution head: `1863bef9b718023d794565f05e4c65814acb5a10`

Binding original pretruth endpoint package:
- source run `32037435314`
- source artifact `9291169452`
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`

Binding result artifact: `9304226655`, digest `sha256:4f5212e897771904e6e385b3b954674067518c2c0b472d13aed727c87ead1248`.

Binding result JSON SHA-256: `a3371b8dbf4fce89a96f3dd6ecfb51857ec3438a4ad6b14dc440fc0eddfabfa3`.

The earlier run `32037435314` was a technical no-result (`KeyError: family_id` before result serialization). Repair 1 added only the identity-only metrics adapter `family_id = frozen family_hash`. Run `32077761371` then stopped before truth because a fresh Recurrent-EOM reconstruction did not reproduce the original comparator/budgets exactly. Repair 2 therefore bound the endpoint directly to the original successful pretruth artifact. No candidate, comparator, order, budget, gate, or metric definition was selected from a scientific outcome.

## Binding target-excluded GMN result

### Fine d=1024

Recurrent-EOM -> annual-density bifiltration equal budget:

- qualified total: `20 -> 12`
- recovered @25/@50/@100/@500: `20/20/20/20 -> 12/12/12/12`
- historical conditional MRR mean: `0.6959325396825397 -> 0.8229166666666666`
- dominant precision mean: `0.3530315709574533 -> 0.9675401881654546`
- fragmentation mean: `1.0 -> 4.1875`
- qualified nonlower panels: `2/8`

### Coarse d=128

Recurrent-EOM -> annual-density bifiltration equal budget:

- qualified total: `94 -> 16`
- recovered @25/@50/@100/@500: `87/94/94/94 -> 12/16/16/16`
- historical conditional MRR mean: `0.23584530975502274 -> 0.5272225128523083`
- dominant precision mean: `0.3396191653933494 -> 0.9454592039316351`
- fragmentation mean: `1.0 -> 16.8125`
- qualified nonlower panels: `0/8`

## Gate outcome

Passed:
- fine MRR non-regression;
- fine precision non-regression;
- coarse MRR non-regression;
- coarse precision non-regression.

Failed:
- fine qualified-total strict improvement;
- fine panelwise qualified non-regression;
- fine fragmentation non-regression;
- coarse qualified-total non-regression;
- coarse panelwise qualified non-regression;
- coarse fragmentation non-regression.

Result: `4/10` gates pass.

## Scientific interpretation

This is a qualitatively different failure from the earlier TopoModal ranking lanes. Keeping the 2022 and 2023 density fields separate through annual-density bifiltration produces extremely pure, very early true matches: both MRR and dominant precision beat Recurrent-EOM at both sparse scales by large margins. The method fails because the equal-budget list repeatedly represents the same physical/topological structures, consuming many slots on fragments and collapsing unique-shower coverage.

Therefore the exact persistence-area-ranked bifiltration catalogue is closed. Do not rescue it by changing persistence-area weights, reranking, threshold grids, scale-specific cutoffs, post-hoc overlap suppression, relaxed gates, or tuned fragment penalties.

The result does support a narrower architectural conclusion for separately preregistered future work: the remaining bottleneck for this topology is **representation/consolidation of repeated fragments**, not raw ranking purity.

The protected inclusive solar-longitude interval `[20°,55°]` remained excluded. SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, DMS, and protected target information were not used.
