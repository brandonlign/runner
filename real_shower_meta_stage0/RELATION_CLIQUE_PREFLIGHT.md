# Hard-negative relation-clique preflight

Status: **killed before the full frozen five-fold benchmark**.

GhostStream was excluded from all training, architecture choices, thresholds, and continuation decisions. The Stage-0 complex folds, episode generator, sporadic exclusions, and baseline definitions were decoded directly from the frozen PR #14 sources before this preflight.

## Fixed preflight result

A reduced runner-equivalent smoke benchmark compared the proposed hard-negative relation-clique scan against the same scan with orbital features removed and against same-episode classical baselines.

| Endpoint | Result |
|---|---:|
| Full relation-clique AUROC | 0.9005 |
| No-orbit relation scan AUROC | 0.9051 |
| Local-density AUROC | 0.8692 |
| DBSCAN AUROC | 0.8785 |
| Fixed-physics scan AUROC | 0.8750 |
| Gain over strongest comparator | -0.0046 |
| Membership F1, k=6/8 | 0.6324 |
| Negative-episode FPR | 0.0417 |
| ECE | 0.1486 |

The untouched ESV control was deliberately skipped in quick mode because the preflight had already failed its required method-specific ablation.

## Kill reason

The orbital/physical relation features did not improve the detector. Removing them slightly increased AUROC. Therefore the apparent performance came from learning a small-subset density scan rather than from transferable physical-coherence learning.

Launching the full five-fold benchmark after seeing this ablation would spend compute on a candidate whose claimed methodological mechanism had already failed. No post-result tuning, alternate feature subset, threshold rescue, or GhostStream application is permitted on this branch.

Verdict: **KILL_RELATION_CLIQUE_FORMULATION**.
