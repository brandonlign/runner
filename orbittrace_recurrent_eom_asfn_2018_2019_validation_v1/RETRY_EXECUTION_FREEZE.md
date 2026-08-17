# ASFN 2018/2019 recurrent-EOM validation — header-repaired retry execution freeze

## Status

Frozen before the next ASFN scientific retry after technical no-result `31834974219`.

The original scientific protocol and runner remain unchanged. The only authorized execution difference is the already-audited runtime wrapper that recognizes the exact hash-prefixed archive header before delegating every other line to the original frozen parser.

## Binding source identities

- original scientific protocol Git blob: `0d90b3db461ff65da3780d507506e4618a2cbf52`;
- original scientific runner Git blob: `8f5699326758dd11cc46f9a209049a8ed61dee3a`;
- promoted recurrent-EOM implementation Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- hash-header wrapper Git blob: `0e5fce5b04959ec45c42bb22ed477e48bdc31bde`;
- wrapper semantic-audit protocol Git blob: `ddc0199a338e50188c005acf9ec9cae2bee77852`;
- wrapper semantic-audit implementation Git blob: `52b235930e6e243caaddff7c7e8884373ccc4313`.

Binding wrapper semantic audit:

- run `31850078483`;
- artifact `9237225355`;
- artifact digest `sha256:7f5d9cea4686e74b1d059366c2c8d73b71b0d29b91eb6fa3e3b0234f7cabeb9b`;
- result SHA-256 `212a52b402187d0bc20c85dc50ba9d0b6b52cbe5126398d9ca7b6b87ffa49ff2`;
- verdict `PASS_ASFN_HASH_HEADER_REPAIR_SEMANTIC_AUDIT`.

The exact ASFN archive remains SHA-256 `c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4` and the exact readme remains SHA-256 `74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf`.

## Execution rule

The retry must execute:

`header_repair_wrapper.py --frozen-source run_validation.py [the original frozen runner arguments]`

The wrapper may change only `header_or_record`. It may not alter or wrap `first_pass`, candidate generation, HDBSCAN, recurrent-EOM extraction, ranking, label unseal, evaluator, or gate.

The first technically valid ASFN endpoint produced under this repaired execution is binding. If it is scientifically valid, no later parser or scientific rescue is authorized from its outcome.

## Scientific invariants

Unchanged from the original protocol:

- years exactly 2018 and 2019;
- inclusive protected interval `[20.0,55.0]` removed before radiant/speed or shower-label decode;
- exact promoted recurrent-EOM HDBSCAN v1 method;
- exact GEO6 representation and speed scale;
- exact HDBSCAN settings;
- exact recurrent annual-normalized EOM minimum;
- exact deterministic ranking;
- complete candidate/prelabel freeze before `shw` access;
- exact frozen ASFN evaluator/gate;
- no result-informed tuning or rescue.

## Firewall

Protected OrbitTrace target information/events, MAARSY, and DMS remain inaccessible. This repair freeze authorizes no access outside the already-frozen ASFN validation boundary.
