# Evaluator repair 1 — rank-density fixed-graph topomodal v1

## Status of run 31968130661

🟡 **NO SCIENTIFIC TRUTH RESULT.**

The first dedicated run successfully completed candidate generation and the independent pretruth seal step. The immutable prelabel is:

- artifact: `9269121527` (`orbittrace-rankdensity-topomodal-v1`)
- prelabel SHA-256: `b6bf31e9add2b9c2e220ccb91d0778859abe86505731d6a0f071ed9eb7c13533`

Before truth opened, the frozen zero-label structural result was already sealed:

- successor pooled fine->coarse mean-best-Jaccard: `0.8009311013016914`
- recurrent-EOM comparator: `0.6152941107471891`
- strict bucket wins: `4/4`
- both preregistered structural generalization gates PASS
- equal-reporting candidate budget sufficient in all eight sparse panels

The evaluator then began loading the unchanged target-excluded GMN catalogue in order to reconstruct the hidden truth mapping. During catalogue download, after reaching 2023-05, the remote GMN server closed the HTTP connection and `gmn_python_api` raised `requests.exceptions.ConnectionError` / `RemoteDisconnected`.

The failure occurred inside `support.parse_catalogue(base)`, before the evaluator had a complete catalogue/truth mapping and before any panel metric, aggregate metric, verdict, or `RANKDENSITY_TOPOMODAL_V1.json` result was produced. The workflow result-contract step was skipped.

Therefore run `31968130661` is an evaluator I/O failure only, not a scientific PASS or FAIL.

## Authorized repair

The successor candidate universe, density values, hierarchy, ranking, structural metrics, candidate budgets, and prelabel are immutable and may not be regenerated or changed.

Evaluator repair 1 is authorized to do only the following:

1. download artifact `9269121527` from run `31968130661`;
2. verify `RANKDENSITY_TOPOMODAL_V1_PRELABEL.json` has SHA-256 exactly `b6bf31e9add2b9c2e220ccb91d0778859abe86505731d6a0f071ed9eb7c13533`;
3. verify the frozen method/firewall/structural-gate/candidate-budget fields in that prelabel;
4. invoke the already-frozen evaluator source blob `b6f25f04e6e81b874ff02b9d89eac96708fa6d34` only;
5. if and only if external GMN HTTP I/O fails, retry the same evaluator against the same immutable prelabel. No candidate-generation code may run in the repair workflow;
6. enforce exactly the original 12-gate result contract.

A retry changes no scientific quantity. It is only transport robustness for reading the same fixed GMN development catalogue and truth mapping.

No change is authorized to the density coordinate, graph, hierarchy, support floor, ranking, sample panels, comparator, truth metric, structural metric, promotion gates, or conditional SonotaCo protocol.

## Firewall

The inclusive protected interval `[20.0,55.0]` remains excluded. No OrbitTrace target information/events, SonotaCo event rows, ASFN/EFN event rows, AMOS scientific data, MAARSY, or DMS may enter this repair.