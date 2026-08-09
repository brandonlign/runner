#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import json
import sys
import zlib
from pathlib import Path

EXPECTED_P11_SHA256="914913d0462ea6793af3836cef945f14a03cca205ac0755ed6cdadb63b8752f9"
EXPECTED_P12_SHA256="78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32"
PATCH_B64='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 fnYbP5Z7oQN0mRkkm00ySvzWuWs qZQhx9EYm qhu5xauZK9k06+N XIy6JUNDnjABIH BWcTPaJ1QXFxhsKal dVL4IuSoy aAqavJtogBJxMdmU/MJxVWP CPZd0MaG5uoG5mzbyk4NdQBqq0NmFDGHC0fK966wF4+BjgciUAEIRyfJ48sLg/L1Gtf x7aT/cMtenlsEWBNJLZaUu/bXSkL5520KpE4va/reKJ1OhjXs yhG0wVPBFQTEsVT8fnooJwhRlCch7YFwztaNLVTbBNWxsjXalcSk0KhtKqAmcBZpMDaYc58LDTUmgouhX7j8d6RUlC/M TW0u7ybn7/m6OYcT7eptiWpmXpo34RI6dYyW0XmFqPWA reD+YS8JpPx8QaActzu1h93FJkcytfGIFDl9rt iljFTGC97uFFwMGcxM8ujDVVeg/WqZw5Ilee32Y6PGtqTXTXStRtsBCVuVp+e9VuGqxodz nzGoQ tlecuDnUfZ8Xg6EaABVVG Gsu/SI4Fiu0rZlm1T15b7bEugzV3eD4kBrQnHLiwv3N2icM8H9yUzXfPYvAy7FyVleretOJ1ZXKbe5+QP rO6s9f7M5nKWxzxWaWxFeFMe/ANLbhEC3dW+xegsmqwtzy1SoU4sN7jAXlE1iuVp6V1qk+hyc/OMcJ6xpgscTuFxb eulfyF7tQA7PswD7LgVYK/Pb27cdxeXNx9u/+3+8+ry9vP5za179fndxWf35vb81v108enXi883v3+4dvEp47uLPy4+Xl1/uri8hVxoYrwtMI7rGKrLmvbeY2B4AdDllfv bVR1iMskhJvtNNWxdwUXZFVRZTTcIeiA39Dljnc2CrUWAyjEM5lA jYwsRhw/wn67SoQyAJmqRcYhI+pmQ8gS5YtAuIz0kwaqcF3k5HzwCH3mfDNcBuy eqBfi78UsH8KMoAajh+pio6am6HTr01474qDjiI0uvXXeoQj1tpVoHUDQLQ5kMYwbfCzlEmUE33TR5EE8gsJL5Q9k62GgS0JoPlWmH1c85wBq6/9hghs1tTFuJ757Pt5ggtY22kzJmwXI1T7ir kvTYunf3nqSiid m9G2cRlASLKu6IbpqUcho xCS2QAPMvVuZuw0FOCgc5aV6eVoFVjTGNeqrG7W1xFd/uW0o23fedkrXu7QbwBsPdxPWzMBxBkI4wDgY++Ur+coYkILtykmnvuQ5zUMA c2irDEO9x3v+puDjRX5k8JpO8ulRvum9GMdBw6y1sR4HX6SRb7dkxyGlH9R0CfyfL8plNlTPr auLctSxM7In1u0oSSwTa/LhH JpKGhTRFobr98dALRau8A5sq5R0HBx0dY+unUiozuJgZah2yQl6zMEkjTPndo wEwcBbKaiKwwwTg+xL1KPIaUpi1xl/JFf4K8hZ/BUmwg9MZcWsyNJKqoTOKjxrUbHxY2LgRevxpb4g/5hv+ooAjCu0seT8+Ja9fP80pVMRBzFTMuHul1lx//Gp2Ojr yn5HkKQ8orcXXr3MRNuBA4gqhVsCRZBuoXHTVT2iYeDVroNl2bIME L0ywJv/HeG/P hpqvA0/wKNjTArVs2IYpEwgJe9iQ667dhqv3uJ66T7F0y81WO2/bXUpUnf1hEX0Pzd/E4tNU53/r3ZxRTzs3/j4HqryVHquhMLP/ArJKTAn'

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p12_patch.py EXACT_P11 OUTPUT")
    source=Path(sys.argv[1]); output=Path(sys.argv[2])
    raw=source.read_bytes()
    actual=sha(raw)
    if actual != EXPECTED_P11_SHA256:
        raise RuntimeError(f"exact P11 source SHA changed: {actual}")
    patches=json.loads(zlib.decompress(base64.b64decode(PATCH_B64)).decode("utf-8"))
    lines=raw.decode("utf-8").splitlines(keepends=True)
    for patch in sorted(patches,key=lambda x:int(x["s"]),reverse=True):
        lines[int(patch["s"]):int(patch["e"])]=str(patch["r"]).splitlines(keepends=True)
    text="".join(lines)
    result=sha(text.encode("utf-8"))
    if result != EXPECTED_P12_SHA256:
        raise RuntimeError(f"P12 transform SHA mismatch: {result}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text,encoding="utf-8")
    print(f"P12_INPUT_P11_SHA256={EXPECTED_P11_SHA256}")
    print(f"P12_OUTPUT_SHA256={result}")
    print("P12_PATCH_SCOPE=exact P11 with only static observation distance replaced by source-year-only linear drift-conditioned 3-D OAS Mahalanobis distance; inherited membership rules/gates unchanged except historical static-representation count assertions become rule-based recomputation")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
