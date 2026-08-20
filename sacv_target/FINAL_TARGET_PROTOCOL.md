# M2D SACV v1 final blind OrbitTrace protocol

Binding prerequisites: PASS_M2D_SACV_V1_GMN_DEVELOPMENT from run 32324386269 and the already-frozen no-post-truth-change SonotaCo SACV check. Parent discovery is the immutable complete 8,469-candidate baseline M2D ranking.

Stage A receives no canonical OrbitTrace package. It reconstructs the same complete target-blind 2022-2023 catalogue used by the original blind M2D scan, applies the exact frozen SACV v1 rule to every original M2D parent at ranks 1-100, and freezes all resulting memberships. Ranks >100 are not computed because the inherited success criterion cannot accept them. No target IDs, target coordinates, prior target reveal, reranking, parent switching, family merging, threshold search, or parameter tuning is permitted.

Only after the Stage-A artifact and SHA-256 are uploaded may Stage B download the immutable canonical package. Stage B performs exact trajectory-ID set intersection only. Success is unchanged: original M2D rank <=100, at least 4 exact 2022 target IDs, at least 4 exact 2023 target IDs, at least 8 exact target IDs total, and exact target F1 >0.5. If no frozen candidate passes, report PARTIAL/NO and do not rescue SACV using the target.
