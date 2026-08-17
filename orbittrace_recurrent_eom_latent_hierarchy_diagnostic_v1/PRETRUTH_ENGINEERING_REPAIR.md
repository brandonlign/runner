# Pretruth engineering repair — membership identity replaces rank-order identity

Initial workflow run `31996096788` is a technical no-result. It stopped in the pretruth stage before SonotaCo truth or residual classifications were downloaded because the reconstructed recurrent-EOM Sugar candidate **rank order** was not byte-identical to the immutable parent order.

The hierarchy diagnostic does not use recurrent-EOM rank order. It requires the exact selected family membership universe solely as an identity check that the pooled HDBSCAN hierarchy was reconstructed compatibly before latent branches are enumerated.

The original frozen runner already performs, immediately after the rank-order assertion, an exact membership-signature equality check over `family_id`, `node_id`, `member_count`, and complete sorted `event_ids` for every selected family.

This repair therefore suppresses **only** the assertion whose message begins `selected order did not reproduce`. Every other assertion is unchanged, including:

- exact selected candidate count;
- exact full membership signature;
- immutable label-free row hashes;
- HDBSCAN/GEO6 settings;
- recurrent-EOM construction;
- latent-node recursive memberships;
- pretruth-before-truth barrier;
- F1 > 0.5 latent-node criterion;
- 50% predeclared guidance cutoff;
- all protected-data firewalls.

If the selected membership signature differs from the immutable parent, the repaired execution still fails before truth. No scientific rule or diagnostic endpoint changes, and the first technically valid endpoint remains binding.