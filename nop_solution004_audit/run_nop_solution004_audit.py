from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path(__file__).with_name("audit_nop_solution004_source.py")
OLD = "shower=next(x for x in payload['data'] if int(x['IAUNo'])==149);rawsol=next(x for x in shower['solution'] if str(x['AdNo']).zfill(3)=='004')"
NEW = "shower=next(x for x in payload['data'] if str(x.get('IAUNo','')).strip().lstrip('+-').isdigit() and int(str(x['IAUNo']).strip())==149);rawsol=next(x for x in shower['solution'] if str(x.get('AdNo','')).zfill(3)=='004')"


def main() -> None:
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    if text.count(OLD) != 1:
        raise RuntimeError(f"Expected exactly one IAUNo selector, found {text.count(OLD)}")
    patched = text.replace(OLD, NEW)
    print("source_sha256", hashlib.sha256(raw).hexdigest())
    print("patched_sha256", hashlib.sha256(patched.encode("utf-8")).hexdigest())
    namespace = {
        "__name__": "__main__",
        "__file__": str(SOURCE.with_name("audit_nop_solution004_runtime.py")),
    }
    exec(compile(patched, namespace["__file__"], "exec"), namespace)


if __name__ == "__main__":
    main()
