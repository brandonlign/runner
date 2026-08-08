from __future__ import annotations

import argparse
import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

from orbittrace_v6_checkpointed_fallback.common import require, sha256_bytes
from orbittrace_v6_exact_fanout_v2.run_exact_center_shard import balanced_center_assignment
from orbittrace_v6_shard0_rescue.run_slice import build_rescue_bins

YEAR = 2023
PARENT_SHARD_COUNT = 6
PARENT_SHARD_INDEX = 0


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def load_with_sha(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes(); sidecar = path.with_suffix(".sha256")
    require(sidecar.exists(), f"missing SHA {path.name}")
    digest = sha256_bytes(raw); require(digest == sidecar.read_text().strip().split()[0], f"SHA mismatch {path.name}")
    return pickle.loads(raw), digest


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument("--preexact-checkpoint",required=True,type=Path); p.add_argument("--slices-dir",required=True,type=Path); p.add_argument("--output",required=True,type=Path); return p.parse_args()


def main() -> int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    pre,pre_sha=load_with_sha(args.preexact_checkpoint)
    require(pre["format"]=="orbittrace-v6-preexact-fanout-v2" and int(pre["year"])==YEAR,"wrong preexact")
    parent_centers=balanced_center_assignment(pre,PARENT_SHARD_COUNT)[PARENT_SHARD_INDEX]
    files=sorted(args.slices_dir.glob("shard0_rescue_*.pkl")); require(bool(files),"no rescue slices")
    rescue_count=None; seen=set(); by_center:dict[float,list[dict[str,Any]]]=defaultdict(list); loads=None
    for path in files:
        obj,_=load_with_sha(path)
        require(obj["format"]=="orbittrace-v6-shard0-rescue-slice-v1" and int(obj["year"])==YEAR,"wrong rescue slice format")
        require(int(obj["parent_shard_index"])==PARENT_SHARD_INDEX and int(obj["parent_shard_count"])==PARENT_SHARD_COUNT,"parent shard identity changed")
        require(obj["preexact_sha256"]==pre_sha and obj["scan_rows_sha256"]==pre["scan_rows_sha256"],"rescue input identity changed")
        require(obj["firewall"]["target_interval_remains_excluded"] is True and obj["firewall"]["labels_not_evaluated"] is True,"rescue firewall failed")
        rc=int(obj["rescue_count"]); rescue_count=rc if rescue_count is None else rescue_count; require(rc==rescue_count,"mixed rescue counts")
        idx=int(obj["rescue_index"]); require(idx not in seen,"duplicate rescue index"); seen.add(idx)
        current=[int(v) for v in obj["estimated_loads"]]; loads=current if loads is None else loads; require(current==loads,"rescue schedules differ")
        for item in obj["slices"]: by_center[float(item["center"])].append(item)
    require(rescue_count is not None and seen==set(range(rescue_count)),f"incomplete rescue indices {seen}")
    expected_bins,expected_loads=build_rescue_bins(pre,rescue_count); require(loads==expected_loads,"rescue load plan changed")

    exact_by_center={}
    for center in parent_centers:
        records=pre["centers"][center]["records"]; pieces=sorted(by_center.get(center,[]),key=lambda x:int(x["record_start"])); require(bool(pieces),f"missing center {center}")
        cursor=0; outputs=[]
        for item in pieces:
            start=int(item["record_start"]); stop=int(item["record_stop"]); require(start==cursor and stop>start,f"gap/overlap center {center}")
            expected=records[start:stop]; require(canonical_sha(expected)==item["records_sha256"],f"slice input changed center {center}")
            exact=item["outputs"]; require([str(r["proposal_anchor_id"]) for r in exact]==[str(r["proposal_anchor_id"]) for r in expected],f"slice output order changed center {center}")
            outputs.extend(exact); cursor=stop
        require(cursor==len(records),f"incomplete center {center}")
        require([str(r["proposal_anchor_id"]) for r in outputs]==[str(r["proposal_anchor_id"]) for r in records],f"assembled order changed center {center}")
        exact_by_center[center]=outputs

    payload={"format":"orbittrace-v6-exact-center-shard-v2","year":YEAR,"shard_index":PARENT_SHARD_INDEX,"shard_count":PARENT_SHARD_COUNT,"preexact_sha256":pre_sha,"scan_rows_sha256":pre["scan_rows_sha256"],"centers":parent_centers,"exact_by_center":exact_by_center,"executor":{"replacement":"multi-runner contiguous record-slice rescue","scientific_body":"immutable original exact_rescore_window_v6; exact outputs reassembled in captured proposal order","rescue_count":rescue_count,"estimated_loads":loads},"firewall":{"target_interval_remains_excluded":True,"labels_not_evaluated":True}}
    raw=pickle.dumps(payload,protocol=pickle.HIGHEST_PROTOCOL); path=args.output/"v6_exact_2023_shard_00.pkl"; path.write_bytes(raw); digest=sha256_bytes(raw); path.with_suffix(".sha256").write_text(digest+"\n")
    print(f"PASS_SHARD0_RESCUE_ASSEMBLY centers={len(parent_centers)} proposals={sum(len(pre['centers'][c]['records']) for c in parent_centers):,} sha={digest}",flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
