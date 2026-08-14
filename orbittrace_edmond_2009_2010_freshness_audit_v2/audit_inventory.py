from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_edmond_2009_2010_freshness_inventory_v2"
TARGET_YEARS = ("2009", "2010")
KNOWN_FAILED_METADATA_RUN = 31205646997


def sh(*args: str, check: bool = True) -> str:
    cp = subprocess.run(args, cwd=ROOT, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout


def github_json(path: str):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise RuntimeError("GITHUB_TOKEN/GITHUB_REPOSITORY missing")
    url = f"https://api.github.com/repos/{repo}/{path.lstrip('/')}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "orbittrace-edmond-freshness-metadata-audit-v2",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def relevant_text(text: str) -> bool:
    low = text.lower()
    return "edmond" in low and any(y in low for y in TARGET_YEARS)


def compact_lines(text: str, limit: int = 200) -> list[str]:
    lines = []
    raw = text.splitlines()
    for i, line in enumerate(raw):
        low = line.lower()
        if "edmond" in low or any(y in low for y in TARGET_YEARS):
            lo, hi = max(0, i - 1), min(len(raw), i + 2)
            snippet = " | ".join(x.strip() for x in raw[lo:hi] if x.strip())
            if snippet and snippet not in lines:
                lines.append(snippet[:1200])
        if len(lines) >= limit:
            break
    return lines


def git_inventory() -> dict:
    # Workflow fetches all remote heads first. Include all local + remote refs.
    refs_raw = sh("git", "for-each-ref", "--format=%(refname)|%(objectname)", "refs/heads", "refs/remotes/origin")
    refs = []
    for line in refs_raw.splitlines():
        if not line.strip() or line.startswith("refs/remotes/origin/HEAD"):
            continue
        ref, sha = line.split("|", 1)
        refs.append({"ref": ref, "sha": sha})

    # Commits whose patches mention EDMOND; inspect both commit metadata and patch.
    # Git's -G uses POSIX regex syntax and does not accept Python-style (?i).
    # --regexp-ignore-case is the semantic-neutral case-insensitive equivalent.
    commits_raw = sh("git", "log", "--all", "--regexp-ignore-case", "--format=%H", "-G", "edmond")
    commit_ids = sorted(set(x.strip() for x in commits_raw.splitlines() if x.strip()))
    exact_year_commits = []
    paths = set()
    for cid in commit_ids:
        show = sh("git", "show", "--no-ext-diff", "--find-renames", "--format=fuller", "--stat", "--oneline", cid)
        names = sh("git", "show", "--no-ext-diff", "--find-renames", "--format=", "--name-only", cid)
        for p in names.splitlines():
            if p.strip():
                paths.add(p.strip())
        # Full patch is requested only for EDMOND-touching commits and remains repo metadata.
        patch = sh("git", "show", "--no-ext-diff", "--find-renames", "--format=fuller", cid)
        if relevant_text(patch):
            exact_year_commits.append(
                {
                    "commit": cid,
                    "summary": show.splitlines()[0] if show.splitlines() else "",
                    "paths": [p for p in names.splitlines() if p.strip()],
                    "snippets": compact_lines(patch, 80),
                }
            )

    # Also inspect every historical file path with EDMOND in its name, at every
    # reachable historical version. This catches separated year/url lines.
    edmond_paths = sorted(p for p in paths if "edmond" in p.lower())
    file_evidence = []
    for p in edmond_paths:
        history = sh("git", "log", "--all", "--format=%H", "--", p)
        for cid in dict.fromkeys(x for x in history.splitlines() if x.strip()):
            cp = subprocess.run(["git", "show", f"{cid}:{p}"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if cp.returncode == 0 and relevant_text(cp.stdout):
                file_evidence.append(
                    {
                        "commit": cid,
                        "path": p,
                        "snippets": compact_lines(cp.stdout, 80),
                    }
                )

    return {
        "ref_count": len(refs),
        "refs": refs,
        "edmond_touching_commit_count": len(commit_ids),
        "exact_year_commit_evidence": exact_year_commits,
        "edmond_named_paths": edmond_paths,
        "exact_year_file_evidence": file_evidence,
    }


def _paged_items(path_prefix: str, key: str, *, max_pages: int = 1000) -> tuple[list[dict], int]:
    items: list[dict] = []
    records_seen = 0
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in path_prefix else "?"
        data = github_json(f"{path_prefix}{sep}per_page=100&page={page}")
        batch = list(data.get(key, []))
        records_seen += len(batch)
        items.extend(batch)
        if len(batch) < 100:
            return items, records_seen
    raise RuntimeError(f"GitHub metadata pagination exceeded safety cap for {path_prefix}")


def _origin_branch_names(git: dict) -> list[str]:
    prefix = "refs/remotes/origin/"
    out = set()
    for row in git["refs"]:
        ref = str(row["ref"])
        if ref.startswith(prefix):
            branch = ref[len(prefix):]
            if "edmond" in branch.lower():
                out.add(branch)
    return sorted(out)


def actions_inventory(git: dict) -> dict:
    # The repository has tens of thousands of Actions runs. Scanning a generic
    # first-N window cannot prove the frozen universe. Instead enumerate the exact
    # union specified by the protocol:
    #   (a) every workflow whose name/path contains EDMOND, across all its runs;
    #   (b) every run on every reachable branch whose name contains EDMOND.
    # The GitHub API supports both queries directly. Deduplicate by run ID.
    workflows, workflow_records_seen = _paged_items("actions/workflows", "workflows")
    edmond_workflows = [
        {
            "id": int(w["id"]),
            "name": str(w.get("name") or ""),
            "path": str(w.get("path") or ""),
            "state": str(w.get("state") or ""),
        }
        for w in workflows
        if "edmond" in (str(w.get("name") or "") + " " + str(w.get("path") or "")).lower()
    ]
    edmond_branches = _origin_branch_names(git)

    runs_by_id: dict[int, dict] = {}
    run_records_seen = 0
    query_receipts = []

    for workflow in sorted(edmond_workflows, key=lambda x: x["id"]):
        path = f"actions/workflows/{workflow['id']}/runs"
        runs, seen = _paged_items(path, "workflow_runs")
        run_records_seen += seen
        query_receipts.append({"kind": "workflow", "workflow_id": workflow["id"], "records_seen": seen})
        for r in runs:
            runs_by_id[int(r["id"])] = r

    for branch in edmond_branches:
        encoded = urllib.parse.quote(branch, safe="")
        path = f"actions/runs?branch={encoded}"
        runs, seen = _paged_items(path, "workflow_runs")
        run_records_seen += seen
        query_receipts.append({"kind": "branch", "branch": branch, "records_seen": seen})
        for r in runs:
            runs_by_id[int(r["id"])] = r

    matches = []
    for rid in sorted(runs_by_id):
        r = runs_by_id[rid]
        name = str(r.get("name") or "")
        branch = str(r.get("head_branch") or "")
        path = str(r.get("path") or "")
        hay = " ".join((name, branch, path)).lower()
        # Fail closed if a targeted API query ever returns a record that is outside
        # the frozen name/path/branch union.
        if "edmond" not in hay:
            raise RuntimeError(f"targeted Actions query returned out-of-universe run {rid}")
        artifacts_data = github_json(f"actions/runs/{rid}/artifacts?per_page=100")
        artifacts = [
            {
                "id": int(a["id"]),
                "name": str(a.get("name") or ""),
                "expired": bool(a.get("expired")),
                "created_at": a.get("created_at"),
                "size_in_bytes": int(a.get("size_in_bytes") or 0),
            }
            for a in artifacts_data.get("artifacts", [])
        ]
        exact_hint = any(y in hay for y in TARGET_YEARS) or any(any(y in a["name"] for y in TARGET_YEARS) for a in artifacts)
        matches.append(
            {
                "run_id": rid,
                "name": name,
                "head_branch": branch,
                "path": path,
                "event": r.get("event"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "head_sha": r.get("head_sha"),
                "artifacts": artifacts,
                "exact_2009_2010_hint": exact_hint,
            }
        )

    return {
        "enumeration_strategy": "UNION_OF_ALL_EDMOND_NAMED_WORKFLOW_RUNS_AND_ALL_EDMOND_BRANCH_RUNS",
        "workflow_metadata_records_scanned": workflow_records_seen,
        "edmond_workflows": sorted(edmond_workflows, key=lambda x: x["id"]),
        "edmond_branches": edmond_branches,
        "targeted_run_metadata_records_scanned_including_query_overlap": run_records_seen,
        "query_receipts": query_receipts,
        "edmond_related_runs": matches,
        "known_failed_metadata_run_present": any(x["run_id"] == KNOWN_FAILED_METADATA_RUN for x in matches),
    }


def exposure_candidates(git: dict, actions: dict) -> list[dict]:
    candidates = []
    # Do not automatically call source mentions exposure. Flag records for adjudication
    # when their text suggests completed data/result/scientific execution.
    scientific_markers = re.compile(
        r"(?i)(result|scientific|events?|rows?|download|artifact|candidate|metric|recovered|f1|pass_|fail_|execution|parsed|catalogue)"
    )
    for item in git["exact_year_commit_evidence"]:
        joined = " ".join(item["snippets"])
        if scientific_markers.search(joined):
            candidates.append({"kind": "git_commit", **item})
    for item in git["exact_year_file_evidence"]:
        joined = " ".join(item["snippets"])
        if scientific_markers.search(joined):
            candidates.append({"kind": "git_file", **item})
    for run in actions["edmond_related_runs"]:
        if run["exact_2009_2010_hint"] and run["conclusion"] == "success":
            candidates.append({"kind": "actions_run_metadata", **run})

    # Deduplicate by compact JSON identity.
    out = []
    seen = set()
    for c in candidates:
        key = json.dumps(c, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    git = git_inventory()
    actions = actions_inventory(git)
    candidates = exposure_candidates(git, actions)

    verdict = (
        "PASS_EDMOND_2009_2010_FRESHNESS_INVENTORY_NO_EXPOSURE_CANDIDATE"
        if not candidates
        else "REVIEW_EDMOND_2009_2010_FRESHNESS_EXPOSURE_CANDIDATES"
    )
    payload = {
        "verdict": verdict,
        "audit_role": "REPOSITORY_AND_GITHUB_METADATA_ONLY_FRESHNESS_INVENTORY",
        "years": [2009, 2010],
        "git": git,
        "actions": actions,
        "exposure_candidates": candidates,
        "event_level_edmond_access": False,
        "external_edmond_request_made": False,
        "historical_scientific_artifact_contents_downloaded": False,
        "historical_edmond_logs_downloaded": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    (OUT / "EDMOND_2009_2010_FRESHNESS_INVENTORY_V2.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "verdict": verdict,
        "ref_count": git["ref_count"],
        "edmond_touching_commit_count": git["edmond_touching_commit_count"],
        "exact_year_commit_evidence_count": len(git["exact_year_commit_evidence"]),
        "exact_year_file_evidence_count": len(git["exact_year_file_evidence"]),
        "workflow_metadata_records_scanned": actions["workflow_metadata_records_scanned"],
        "edmond_workflows": len(actions["edmond_workflows"]),
        "edmond_branches": len(actions["edmond_branches"]),
        "edmond_related_actions_runs": len(actions["edmond_related_runs"]),
        "exposure_candidate_count": len(candidates),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
