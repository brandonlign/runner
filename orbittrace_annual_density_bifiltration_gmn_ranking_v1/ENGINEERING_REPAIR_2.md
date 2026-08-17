# Annual-density bifiltration GMN ranking v1 — engineering repair 2

## Status

**EXECUTION/PROVENANCE REPAIR ONLY. SCIENTIFIC PROTOCOL UNCHANGED.**

Repair 1 fixed the evaluator's identity-only `family_id` interface and added an exact SHA lock to the successful pretruth endpoint package from run `32037435314`.

The first repaired attempt, run `32077761371`, intentionally stopped before truth because a fresh reconstruction of the prelabel did not reproduce that exact SHA.

## What the failed reconstruction showed

The reconstructed target-excluded annual event universes were identical in all eight sparse panels, and every frozen annual-density bifiltration candidate list was exactly identical in membership and order to the original prelabel.

However, recomputing the Recurrent-EOM comparator through the current runtime was not byte/scientifically identical to the original pretruth comparator. In particular, the equal-budget K changed in two panels (`d=128,b=2: 38 -> 39`; `d=1024,b=0: 8 -> 9`) and several comparator memberships changed slightly in other panels.

Therefore the reconstructed prelabel is rejected. No shower truth was opened in run `32077761371`.

## Sole repair

Do not reconstruct the endpoint prelabel at all.

Instead, bind evaluation directly to the original successful pretruth artifact created before the first truth attempt:

- source run: `32037435314`
- artifact: `9291169452`
- artifact name: `orbittrace-annual-density-bifiltration-gmn-ranking-v1-prelabel`
- artifact ZIP digest: `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`

That original prelabel already passed the frozen prelabel job and firewall before the initial evaluator opened truth. It contains both the frozen annual-density bifiltration catalogue and the exact Recurrent-EOM comparator/budget used by the preregistered endpoint.

The evaluation job must download and verify those exact bytes. It may not regenerate candidates, comparator families, budgets, annual event universes, or ranking.

## Scientific invariants

This repair changes none of the following:

- annual-density bifiltration candidate membership or order;
- Recurrent-EOM comparator membership or order;
- equal-budget K;
- annual event universes;
- truth mapping or match definition;
- conditional MRR definition frozen by the original protocol;
- any of the ten promotion gates;
- target firewall or external-data access.

The only evaluator-side adapter remains Repair 1's `family_id = family_hash`, which the frozen truth implementation does not read when computing any metric.

## Binding rule

Run `32077761371` is a technical pretruth stop and has no scientific verdict. The first later execution that verifies the exact original prelabel, completes result serialization, and enforces all ten frozen gates is the binding scientific result.
