# ASFN 2018/2019 validation — required README receipt argument repair

## Status

Frozen before activation of the transport-only retry and before any new ASFN archive acquisition.

Review of the already-frozen scientific runner found that its CLI requires `--readme-receipt`, and that the prior header-repaired workflow omitted that required argument. The prior run `31850281138` never reached scientific execution because the NASA archive transfer timed out with zero bytes, so this omission has produced no scientific endpoint and no data-informed information.

This is an execution-contract repair only. The scientific runner remains byte-identical at Git blob `8f5699326758dd11cc46f9a209049a8ed61dee3a` and independently requires the README bytes to hash exactly to:

`74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf`

## Exact repair

After, and only after, the exact frozen NASA archive has been fully transferred and verified to SHA-256:

`c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`

extract exactly one ZIP member whose basename is:

`nasfn_2013-2019_readme.txt`

Write those bytes unchanged to a local receipt file, verify the receipt SHA-256 is exactly the pinned README hash above, and pass that path as the frozen runner's required `--readme-receipt` argument.

No README-derived value may alter a method choice. No scientific data-member byte may be opened by this repair step. The frozen runner will independently re-verify the archive and README identities before its existing staged parser executes.

## Scientific invariants

This repair changes none of the following:

- ASFN years 2018 and 2019;
- inclusive protected interval `[20.0,55.0]`;
- event eligibility;
- GEO6 representation;
- HDBSCAN parameters;
- recurrent-EOM construction or ranking;
- prelabel-before-`shw` boundary;
- evaluator or PASS/FAIL gate;
- hash-header wrapper semantics;
- first-technically-valid-endpoint-is-binding rule;
- no-rescue rule.

## Firewall

This repair itself authorizes no network access, ASFN event-value access, target information/event access, MAARSY access, or DMS access. It only defines how the already-required, already-pinned README receipt is supplied if the separately frozen exact archive transfer succeeds.