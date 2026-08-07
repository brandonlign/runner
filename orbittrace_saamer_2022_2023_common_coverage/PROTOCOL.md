# SAAMER 2022–2023 common-coverage structural adjudication

## Status

Frozen after the first structure-only audit and before any SAAMER 2022/2023 meteor scientific value is decoded.

The first structure-only audit was intentionally strict and failed only because the official 2023 annual archive ends after October, whereas the official 2022 archive contains January–December. The preserved artifact states that no scientific, orbital, shower-label, target-region, or OrbitTrace target value was read.

This adjudication is **metadata-only**. It consumes only the first audit artifact and does not download or open either SAAMER archive.

## Immutable first-audit inputs

- structure run: `31211663133`;
- structure artifact: `9006922387`;
- artifact ZIP SHA-256: `cb709dc9e9157c587c54f95595181a3ee3d4b61e27b8ec1b8a401ebc74fa22d9`;
- 2022 archive SHA-256: `8347c4fde8d1035702f74002321e55d66df42055a0d3bf46424fd286b6e861f7`;
- 2023 archive SHA-256: `0220c5cb32eb4fdaaaca8773de03512864246c7a91c8211e68cc5d5f54f16f8a`;
- legend SHA-256 both years: `afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b`;
- all present meteor DAT records have exactly 16 whitespace-separated tokens;
- 2022 contains exactly January–December nominal-year members;
- 2023 contains exactly January–October nominal-year members;
- no unexpected regular ZIP members were present.

## Frozen correction

For any later scientific external validation using this pair, use **only the common nominal-month coverage January through October in both 2022 and 2023**.

- 2022 November and December are excluded by file identity before any meteor row in those members is decoded.
- No alternate month subset is evaluated.
- The 10,000-events-per-10°-solar-longitude-bin identity-hash normalization remains unchanged from the 2020/2021 external protocol.
- The v6 detector, family construction, multiplicity ranking, D_SH post-ranking corroboration, `N>=100` family power gate, `Q>=30` corroborated-family power gate, top-K rule, and all scientific pass gates remain unchanged.

This is a coverage-transport correction caused solely by archive member availability metadata, not by any meteor value or scientific result.

## Pass condition

Pass iff the preserved first-audit artifact exactly confirms the hashes/schema/boundaries above and the intersection of nominal-year month members is exactly January–October.

A pass authorizes freezing the scientific 2022/2023 external-validation protocol with common Jan–Oct coverage. It does not authorize reading OrbitTrace's target interval or altering any scientific gate.
