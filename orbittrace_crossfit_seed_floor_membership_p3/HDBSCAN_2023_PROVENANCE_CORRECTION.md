# P3 matched-literature HDBSCAN-2023 provenance correction

Status: frozen while authoritative P3 development run `31291214704` remains unresolved and before any P3 matched-literature execution.

The initial P3 literature protocol copied the historical HDBSCAN-2023 assignment SHA `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60` from the pre-verification v8 comparison text. That artifact was later superseded, independently of P3, by the already-completed blind-safe HDBSCAN-2023 assignment verification in the v8 literature lineage.

For every P3 matched-literature execution, the **only valid HDBSCAN-2023 assignment** is therefore:

- exact-row event/assignment artifact SHA-256 `35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761`;
- exact row count 26,460;
- same 2023 SonotaCo exact-row semantics used by the final v8 matched benchmark and the source-only P2 matched implementation.

The old `7dbb...` artifact is not an allowed alternative and cannot be selected by outcome. HDBSCAN-2025 and both Sugar artifacts remain unchanged.

This correction changes only competitor provenance to the already-established blind-safe canonical artifact. It changes no P3 source, event-universe definition, truth mapping, size bin, metric, superiority threshold, promotion rule, target firewall, or comparator method.
