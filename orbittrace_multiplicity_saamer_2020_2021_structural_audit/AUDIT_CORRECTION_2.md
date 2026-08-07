# Structure-audit correction 2 — monthly `.dat` layout plus `legend.inf`

The corrected structure-only run `31206598202` established, without reading any meteor values, that the official SAAMER annual ZIPs are not single-table archives. They contain:

- one small `legend.inf` schema/legend file;
- monthly `SAA<mon><year>.dat` data members;
- 2020 additionally includes `SAAdec2019.dat`, consistent with the MDC catalogue beginning on 31 December 2019.

Archive hashes were structurally recorded as:

- 2020: `208938b6ed6c504d77eb96ae1d9a867f5957fcba48076fd1bac9632c24ff4933`
- 2021: `41a1aa7d568c98f273087fd2648cf6e9aa365373bf25b3db36d54ea987dd727c`

The next structure-only audit may read the complete 293-byte `legend.inf` file because it is schema metadata, not a meteor record. It may scan `.dat` files only as opaque physical lines to count rows, byte lengths, and whitespace-token counts; token contents may not be decoded, retained, compared, printed, or used. The audit may verify that the legend names the MDC-documented method fields `LS`, `RA`, `DEC`, `Vg`, and `Sh` and that the monthly files have stable structural signatures.

No scientific meteor value, shower-label value, detector score, excluded-target-region value, or OrbitTrace information may be accessed.
