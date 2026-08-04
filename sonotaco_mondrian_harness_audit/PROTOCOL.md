# SonotaCo Mondrian adapter: no-data PR #38 harness audit

Status: frozen before any SonotaCo scientific score, window, calibration sample, comparator, fold, or endpoint is computed.

## Purpose

Decode and inspect the exact coverage-normalized Mondrian quartet scorer from PR #38 so a survey adapter can reuse its physical geometry, quartet statistic, calibration functions, comparators, folds, endpoints, and reporting logic without reconstructing them from memory.

## Allowed outputs

- exact decoded scorer source and SHA-256;
- module-level imports, constants, classes, function names, signatures, line ranges, and docstrings;
- parser/CLI argument definitions;
- static call graph;
- source excerpts grouped by function;
- Python compile result.

## Forbidden operations

This audit may not download or open any GMN or SonotaCo data, action artifact, label file, event table, calibration bank, positive or negative window, score, comparator output, or scientific result. It may not import and execute the scorer module. It performs static inspection only.

## Pinned source

- exact decoded scorer SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- `part00.b64`: `6b5a5a449f381b6d47ecde6981ff301aee47927de1763cd124ca165713230104`;
- `part01.b64`: `3460d412c23e45b1fa729af769a192ea11554d278b49cd38bb13c12e4496fb79`;
- `part02.b64`: `f2853f0e5c3f6e0b8d127d919f2d7bf53ca284e6f33ee065ebea81e4477582ad`;
- `part03.b64`: `9104365b8e786e3e0c33aa4e1badd01c96c02404879898221694b1e07a134b42`.

A successful audit authorizes only writing a separately frozen SonotaCo-2025 scientific development protocol and adapter. It does not authorize executing that study or touching the reserved SonotaCo-2024 panel.