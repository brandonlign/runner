#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_INPUT_SHA256 = "169ed0a276cdcae628cd830130cfb03d6511a972df50d4dc10ffddfc1c8e05da"

BEFORE_COVARIANCE = '''    sign, logdet = np.linalg.slogdet(cov)
    if sign > 0 and np.isfinite(logdet):
        inverse = np.linalg.inv(cov)
        inverse_method = "inverse"
    else:
        inverse = np.linalg.pinv(cov)
        inverse_method = "moore_penrose_pseudoinverse"
    require(np.all(np.isfinite(inverse)), "non-finite covariance inverse")
    return center, inverse, {
        "seed_count": len(rows),
        "oas_shrinkage": float(model.shrinkage_),
        "covariance": cov.tolist(),
        "inverse_method": inverse_method,
    }
'''

AFTER_COVARIANCE = '''    covariance_rank = int(np.linalg.matrix_rank(cov))
    if covariance_rank < cov.shape[0]:
        inverse = np.linalg.pinv(cov)
        inverse_method = "moore_penrose_pseudoinverse"
    else:
        inverse = np.linalg.inv(cov)
        inverse_method = "inverse"
    require(np.all(np.isfinite(inverse)), "non-finite covariance inverse")
    return center, inverse, {
        "seed_count": len(rows),
        "oas_shrinkage": float(model.shrinkage_),
        "covariance": cov.tolist(),
        "covariance_rank": covariance_rank,
        "inverse_method": inverse_method,
    }
'''

BEFORE_WINDOW = '''    return delta <= WINDOW_HALF_WIDTH_DEG + 1e-15
'''
AFTER_WINDOW = '''    return delta <= WINDOW_HALF_WIDTH_DEG
'''


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_protocol_precision_patch_v2.py INPUT OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    if digest(raw) != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"unexpected P2 v2 input SHA256: {digest(raw)}")
    text = raw.decode("utf-8")
    if text.count(BEFORE_COVARIANCE) != 1:
        raise RuntimeError("covariance precision anchor not unique")
    if text.count(BEFORE_WINDOW) != 1:
        raise RuntimeError("window precision anchor not unique")
    patched = text.replace(BEFORE_COVARIANCE, AFTER_COVARIANCE, 1).replace(BEFORE_WINDOW, AFTER_WINDOW, 1)
    reverted = patched.replace(AFTER_WINDOW, BEFORE_WINDOW, 1).replace(AFTER_COVARIANCE, BEFORE_COVARIANCE, 1)
    if reverted != text:
        raise RuntimeError("P2 precision patch is not exactly reversible")
    output.write_text(patched, encoding="utf-8")
    print(f"P2_PRECISION_PATCH_INPUT_SHA256={EXPECTED_INPUT_SHA256}")
    print(f"P2_PRECISION_PATCH_OUTPUT_SHA256={digest(patched.encode('utf-8'))}")
    print("P2_PRECISION_PATCH_SCOPE=machine-precision covariance fallback and exact 5-degree boundary only; no scientific parameter changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
