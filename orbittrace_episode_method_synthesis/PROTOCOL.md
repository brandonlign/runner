# OrbitTrace episode-method final synthesis

## Purpose

Synthesize the completed fixed4, Brown-family wavelet, symmetric hybrid, and asymmetric sparse-tail experiments without rerunning or modifying any method.

This stage is artifact-only. It may not open a meteor catalogue, generate an episode, recompute a component score, change a margin, replace an endpoint, or reinterpret a frozen prospective decision.

## Exact evidence

- SonotaCo 2025 fixed4/wavelet development artifact `8969020016`, ZIP SHA-256 `c8d72fa8b051da05c0e4701a48302f97bf53232bd623df30a6953e05b8522232`;
- SonotaCo 2023 fixed4/wavelet transfer artifact `8969274303`, ZIP SHA-256 `d00faaf9d781b988bbab0af09e1e27ddf0a824be63f96778bf295b4bf56c404b`;
- SonotaCo 2022 prospective symmetric-hybrid artifact `8970137965`, ZIP SHA-256 `5cc0404f486e7ca060349345e42b042201a0a4732dfe680c98b1243d0ae1da43`;
- sparse-tail development artifact `8970482364`, ZIP SHA-256 `8ed861bc9468d61e474ae37b86a1871200fe17abc630b9172fb00e236f12b075`;
- SonotaCo 2021 prospective sparse-tail artifact `8971081478`, ZIP SHA-256 `7eb18dd939714ac1656dd2a1cfbef9ff29fece93cfa97a55f848598380c7fffd`.

## Fixed decision hierarchy

1. A method may be called the primary general episode detector only if it has the strongest prospective weak AUROC while retaining calibrated false-positive control.
2. A method may be called a complementary sparse detector if it repeatedly contributes superior k=4 sensitivity or lower false-positive rates without winning general ranking.
3. An ensemble may be promoted only when its own frozen prospective decision is promotion.
4. Retrospective development gains cannot override a prospective retain/reject decision.

## Allowed final classifications

- `WAVELET_PRIMARY_FIXED4_COMPLEMENTARY_NO_PROMOTED_ENSEMBLE`;
- `FIXED4_PRIMARY_NO_PROMOTED_ENSEMBLE`;
- `PROMOTED_ENSEMBLE_PRIMARY`;
- `NO_STABLE_EPISODE_METHOD_CONCLUSION`.

The synthesis must preserve that the Brown-family wavelet is a literature-derived comparator, not an OrbitTrace-original method. A wavelet-primary conclusion therefore does not create a novel-method claim. It instead fixes the honest methodological boundary and prevents overstating the failed ensembles.

This synthesis is distinct from catalogue-scale family construction and ranking, which remain under separate development.