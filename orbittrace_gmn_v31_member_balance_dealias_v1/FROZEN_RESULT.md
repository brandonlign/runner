# OrbitTrace GMN v31 member-balance de-alias v1 — binding result

## Verdict

🔴 `FAIL_GMN_V31_MEMBER_BALANCE_DEALIAS_V1`

The exact duplicate-coordinate audit is valid, but removing the duplicate worsened the binding top-100 and precision gates. Exact v31 remains unchanged.

## Frozen provenance

- pre-outcome protocol commit: `b198758c476ac65ce8c0825f52b37a18d9afd9f4`
- authoritative offline package artifact: `9167087908`
- exact parent feature SHA-256: `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`
- exact parent margin SHA-256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- binding result JSON SHA-256: `b7cddb3519d88f94f7127c9d4e32741cf8898a6f0acaa6fccd762a328f8693e8`
- candidate 22D matrix SHA-256: `f32e85fe126adcf522b0e436cd3fe90e63edf268e84aae7ac22d73ec5acd2896`
- candidate OOF margin SHA-256: `950b2881bba10611a2a35573c19db67227783eb7b61fda264e4626dc6bb73063`
- candidate local-order SHA-256: `91912518f2bec7c760a442a830e137b65bce0adf9020bdb4e716f811e5332b6e`
- candidate fused-order SHA-256: `0e762efabdc2d3febd1c66c12e201469c9883c07629ba67ac988b67ed60e35c3`

The evaluator first reproduced the exact v31 23D matrix and parent margin hash, then reproduced the hard and fused parent controls before the sole de-alias correction.

## Label-free audit fact

Exact v31 columns 8 and 12 are bit-for-bit identical for all 226 families (`max_abs_difference=0`, differing rows `0`). They independently entered the assembled schema as structural `member_year_balance` and cohesion `member_count_year_balance`, but represent the same annual member-count balance observable.

Columns 17–20 are also identical to one another, but all four are constant zero and therefore inert under exact v31 scaling/distance; they were deliberately left untouched.

## Sole frozen change

`X22 = np.delete(X23, 12, axis=1)`

Column 8 was retained unchanged. No other feature, fold, scale, metric, k, diversity, fusion, candidate, or evaluator rule changed.

## Binding metrics

Exact v31 fused parent:
- recovered@25: `23`
- recovered@50: `41`
- recovered@100: `66`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified matches: `95`

De-aliased 22D candidate:
- recovered@25: **`24`** — +1
- recovered@50: **`42`** — +1
- recovered@100: **`65`** — -1, FAIL
- top-100 dominant precision: **`0.7211426277358213`** — lower, FAIL
- MRR: **`0.05038655918798809`** — improved
- qualified matches: **`95`** — preserved

Therefore four gates pass and two fail. The representation change is not promotable.

## Interpretation

The duplicate coordinate is a genuine schema alias, but in the current v31 local geometry its effective extra weighting happens to support the top-100 objective. That empirical fact does **not** authorize tuning the duplicate's weight. Under the frozen protocol the only scientifically valid conclusion is to preserve exact v31 and close this de-aliasing successor.

Do not try half-weighting, deleting the other copy, averaging the copies, removing additional coordinates, correlation-based pruning, PCA/whitening, metric changes, or any other rescue listed in the protocol.

No SonotaCo benchmark is authorized.

## Firewall

Binding calculation used only the frozen offline 226-family package and accessed no raw event rows, SonotaCo truth, protected target-region events, OrbitTrace target information, MAARSY, or DMS.
