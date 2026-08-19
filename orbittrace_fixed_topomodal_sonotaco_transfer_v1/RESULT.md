# OrbitTrace fixed support-resolved TopoModal → SonotaCo transfer v1 — binding result

## Verdict

`FAIL_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1`.

Binding workflow run: `32229294081`

Binding artifact: `9356655334` (`orbittrace-fixed-topomodal-sonotaco-transfer-v1-32229294081`)

Artifact digest: `sha256:2695f31af771d0824859426384cf599576c650a285d208972834871e66b3d560`

The exact GMN-frozen support-resolved TopoModal method was transferred without SonotaCo tuning to the exact 29,246-event symmetric-v2 common universe and scored with the unchanged Hungarian macro-F1 evaluator.

## Primary result

| method | mean test AUC macro-F1 | mean K40 macro-F1 | total recovered @40 | mean native macro-F1 |
|---|---:|---:|---:|---:|
| tuned HDBSCAN | **0.345475559012312** | **0.46086713246967964** | **52** | 0.4762894120871253 |
| fixed support-resolved TopoModal | 0.33211204306639563 | 0.4455723912337259 | 50 | **0.7266723655790133** |
| recurrent-EOM | 0.3316416828251373 | 0.4319510872281714 | 48 | 0.4713058859394265 |
| Sugar | 0.2524830382000305 | 0.35121785985472137 | 39 | 0.43624045003398304 |

Primary AUC delta versus tuned HDBSCAN: `-0.013363515945916338`.

The fixed transfer therefore ranks second and does not satisfy the preregistered strict AUC win condition.

## Annual fixed-transfer result

2013:
- AUC macro-F1: `0.3273273678885529`
- K10/K20/K30/K40 macro-F1: `0.1755326936 / 0.2910757998 / 0.4033665041 / 0.4393344740`
- recovered at K10/K20/K30/K40: `10 / 17 / 24 / 27`
- native macro-F1: `0.7212989263`
- native recovered F1>0.5: `42`

2014:
- AUC macro-F1: `0.33689671824423834`
- K10/K20/K30/K40 macro-F1: `0.1880816050 / 0.2978038430 / 0.4098911165 / 0.4518103084`
- recovered at K10/K20/K30/K40: `10 / 15 / 21 / 23`
- native macro-F1: `0.7320458049`
- native recovered F1>0.5: `39`

Pooled support-resolved catalogue size: `888` candidates.

## Interpretation

This is **not** a primary benchmark improvement. Tuned HDBSCAN remains the winner.

The large native-catalogue macro-F1, however, is a cross-survey diagnostic that the fixed TopoModal candidate set contains substantially more of the catalogue truth than the current top-K order exposes. The same candidate-generation-versus-ranking split was previously seen on target-excluded GMN. That motivates testing only ranking mechanisms that were already frozen without SonotaCo access; it does not authorize a SonotaCo-informed reranker.

The exact fixed modal-contrast transfer is closed. No radius, support, physical bandwidth, cut, modal-contrast score, budget, event-universe, truth, or evaluator change is permitted as a rescue of v1.
