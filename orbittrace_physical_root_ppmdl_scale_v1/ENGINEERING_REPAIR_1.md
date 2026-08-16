# Engineering repair 1 — immutable graph-tool release image metadata

## Classification

**ENGINEERING NO-RESULT REPAIR ONLY.**

Initial workflow run `31970709438`, job `95222643239`, never completed a single planted-partition fit and never emitted a diagnostic metric or `PHYSICAL_ROOT_PPMDL_SCALE_V1.json` result.

The run successfully:

- audited every frozen scientific source/input dependency;
- pulled the protocol-specified official Docker tag `tiagopeixoto/graph-tool:release-2.98`;
- recorded its immutable repo digest as `sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7`;
- loaded the unchanged target-excluded GMN catalogue;
- constructed the first frozen `d=128,b=0` physical graph (`n=5567`, `64247` simple undirected edges).

It then stopped **before the first `minimize_blockmodel_dl()` invocation** because the protocol-specified Docker image reports internal `graph_tool.__version__` as:

`2.99dev (commit c049a734, Thu Aug 21 21:35:01 2025 +0200)`

rather than a string beginning with `2.98`.

No PPMDL candidate, partition, cross-scale Jaccard, comparator metric, shower truth, SonotaCo row, or protected target information was produced/accessed.

## Exact repair

The Docker **image bytes are unchanged** from the predeclared `release-2.98` tag. This repair makes those exact bytes authoritative by replacing the mutable tag reference in scientific execution with the observed immutable digest:

`tiagopeixoto/graph-tool@sha256:e12ed85b23e1068eec883bbffeafc7cc36ce461f88ee26e0b3ef20bfcd5508f7`

The internal-version guard is changed only from the incorrect packaging expectation `startswith('2.98')` to the exact observed build identity:

`startswith('2.99dev (commit c049a734')`.

The pre-data image-version probe also adds Docker `-i` so its heredoc is actually executed and verifies the exact same build identity before GMN access.

## Scientific invariants

Unchanged:

- frozen `PROTOCOL.md` scientific method and motivation;
- exact #1284 physical embedding and radius-1 simple graph;
- connected-component outer boundaries;
- `PPBlockState` model class;
- `minimize_blockmodel_dl()` with no scientific argument overrides;
- deterministic one-seed-per-component rule;
- no restarts/model averaging;
- support floor 4;
- all eight frozen subsets;
- exact recurrent-EOM comparator;
- exact #1284 cross-scale metric;
- all five frozen interpretation gates;
- complete target/label firewall.

This repair is permitted because the first run produced no technically valid model fit or scientific endpoint. It does not create a second scientific chance.