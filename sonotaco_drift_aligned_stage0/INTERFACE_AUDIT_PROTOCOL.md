# SonotaCo drift-aligned inherited-interface audit

Status: frozen before any meteor archive is downloaded or detector score is computed.

This source-only extension decodes the exact baseline, Mondrian scorer, and SonotaCo adapter sources used by PRs #69, #109, and #112. It preserves their source and AST signatures so a drift-aligned candidate can use verified event fields, episode construction, fold assignment, and calibration interfaces.

Required exact SHA-256 values:

- baseline: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`
- scorer: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`
- adapter: `5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`

The workflow may compile and AST-parse source only. It may not request a SonotaCo archive, mapping artifact, meteor row, label value, score, fold result, or endpoint. SonotaCo 2024 and GhostStream remain untouched.
