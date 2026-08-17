# EFN 2017/2018 source-pin chronology clarification

**Status: POST-HOC PROVENANCE CLARIFICATION ONLY. Scientific method unchanged.**

This file corrects an inaccurate chronology statement introduced in commit `81c48dc34c409486ff1666af7cee15595e4bcd1c`. That commit incorrectly described this note as occurring before EFN event access. In fact, the EFN branch had already completed its staged Stage-1 blind receipt, retained-only Stage-2 geometry receipt, and binding pretruth candidate freeze earlier on 2026-08-14.

The original protocol contains a transcription error in one provenance line:

- malformed text in `PROTOCOL.md`: `30ac3fa3bc47910370df5282258e3d1429fbe00d67`
- authoritative promoted recurrent-EOM implementation blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Crucially, this transcription error did **not** alter the binding candidate-generation execution. The binding pretruth freeze records the actually imported/pinned recurrent-EOM source as the correct promoted blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Binding pretruth run: `31842380038`; artifact: `9234706525`; pretruth SHA-256: `2038b2ca3f2d5695f407e97eed278dc5a4220965cdec7581e866daa7f4b4a0d4`.

An earlier file, `SOURCE_PIN_REPAIR.md`, already documented the malformed protocol string as a transcription error before the scientific candidate-generation stage. Stage 1 and Stage 2 did not execute recurrent-EOM and therefore did not depend on this source identity.

This clarification changes no code, method, representation, HDBSCAN parameter, recurrent-stability formula, ranking rule, evaluator, gate, year, EFN field mapping, retained IDs, geometry values, pretruth payload, or firewall rule. The malformed protocol text is preserved historically and must never be interpreted as an alternate method choice.

No EFN Stage-3 shower label has been accessed by this clarification.
