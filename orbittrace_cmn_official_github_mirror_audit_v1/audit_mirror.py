#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import subprocess
import urllib.parse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPOSITORY = "CroatianMeteorNetwork/CMN-codes"
COMMIT = "2077285b66b6fd8df633ff0aec5ef0af0bf24ef6"
PAGE_PATH = "CMN website/downloads/downloads.html"
SITE_BASE = "http://cmn.rgn.hr/downloads/downloads.html"
SITE_HOST = "cmn.rgn.hr"
MIRROR_PREFIX = "CMN website"
ORBIT_CUE = "orbitcat"
FORMATS = {"zip", "csv", "txt", "dat", "xls", "xlsx", "rar", "7z", "gz", "bz2"}
OUT = Path("output")


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def load_tree(repo: Path) -> dict[str, tuple[str, str]]:
    raw = git(repo, "ls-tree", "-r", "-z", COMMIT)
    out: dict[str, tuple[str, str]] = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        _mode, typ, sha = meta.decode("ascii").split(" ", 2)
        out[path.decode("utf-8", errors="strict")] = (typ, sha)
    return out


def href_to_repo_path(href: str) -> tuple[str, str] | None:
    absolute = urllib.parse.urljoin(SITE_BASE, href)
    parsed = urllib.parse.urlparse(absolute)
    host = (parsed.hostname or "").lower()
    if host and host != SITE_HOST:
        return None
    site_path = parsed.path or ""
    if not site_path.startswith("/"):
        site_path = "/" + site_path
    repo_path = posixpath.normpath(MIRROR_PREFIX + "/" + site_path.lstrip("/"))
    if repo_path == MIRROR_PREFIX or not repo_path.startswith(MIRROR_PREFIX + "/"):
        return None
    ext = Path(site_path).suffix.lower().lstrip(".")
    return repo_path, ext


class OrbitSectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cue_found = False
        self.active = False
        self.cue_heading_level: int | None = None
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    @staticmethod
    def _heading_level(tag: str) -> int | None:
        if len(tag) == 2 and tag[0].lower() == "h" and tag[1].isdigit():
            n = int(tag[1])
            if 1 <= n <= 6:
                return n
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        a = {str(k).lower(): ("" if v is None else str(v)) for k, v in attrs}
        ident = a.get("id", "").lower()
        name = a.get("name", "").lower()
        cue_here = ident == ORBIT_CUE or name == ORBIT_CUE
        level = self._heading_level(t)

        if cue_here:
            self.cue_found = True
            self.active = True
            self.cue_heading_level = level
        elif self.active:
            named_boundary = bool(ident or name)
            heading_boundary = level is not None and self.cue_heading_level is not None and level <= self.cue_heading_level
            if named_boundary or heading_boundary:
                self.active = False

        if t == "a" and self.active and "href" in a:
            self._href = a.get("href", "")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = " ".join("".join(self._text).split())
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mirror-repo", type=Path, required=True)
    p.add_argument("--output", type=Path, default=OUT)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req((a.mirror_repo / ".git").exists(), "mirror git repository missing")
    actual_commit = git(a.mirror_repo, "rev-parse", COMMIT).decode().strip()
    req(actual_commit == COMMIT, "official mirror commit pin changed")

    tree = load_tree(a.mirror_repo)
    req(PAGE_PATH in tree and tree[PAGE_PATH][0] == "blob", "pinned downloads page missing from mirror tree")
    page_blob_sha = tree[PAGE_PATH][1]

    # This is the sole non-metadata blob read permitted by the protocol.
    page = git(a.mirror_repo, "show", f"{COMMIT}:{PAGE_PATH}")
    page_sha256 = hashlib.sha256(page).hexdigest()
    text = page.decode("utf-8", errors="replace")

    parser = OrbitSectionParser()
    parser.feed(text)

    structural_candidates: list[tuple[str, str]] = []
    ext_counts: Counter[str] = Counter()
    for href, link_text in parser.links:
        mapped = href_to_repo_path(href)
        if mapped is None:
            continue
        repo_path, ext = mapped
        searchable = f"{urllib.parse.urlparse(href).path} {link_text}".lower()
        if "orbit" not in searchable or ext not in FORMATS:
            continue
        structural_candidates.append((repo_path, ext))
        ext_counts[ext] += 1

    # De-duplicate by normalized repository path before testing tree resolution.
    structural_candidates = sorted(set(structural_candidates), key=lambda x: x[0].encode("utf-8"))
    resolved: list[tuple[str, str, str]] = []
    for repo_path, ext in structural_candidates:
        obj = tree.get(repo_path)
        if obj is not None and obj[0] == "blob":
            resolved.append((repo_path, ext, obj[1]))

    selected_path_sha256 = None
    selected_blob_sha = None
    if resolved:
        resolved.sort(key=lambda x: x[0].encode("utf-8"))
        selected_path_sha256 = hashlib.sha256(resolved[0][0].encode("utf-8")).hexdigest()
        selected_blob_sha = resolved[0][2]

    result: dict[str, Any] = {
        "stage": "CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT_V1",
        "verdict": None,
        "official_repository": REPOSITORY,
        "pinned_commit": COMMIT,
        "downloads_page_git_blob_sha": page_blob_sha,
        "downloads_page_sha256": page_sha256,
        "orbitcat_cue_present": parser.cue_found,
        "structural_candidate_link_count": len(structural_candidates),
        "candidate_extension_counts": {ext: int(ext_counts.get(ext, 0)) for ext in sorted(FORMATS)},
        "resolved_candidate_blob_count": len(resolved),
        "selected_candidate_path_sha256": selected_path_sha256,
        "selected_candidate_git_blob_sha": selected_blob_sha,
        "raw_html_emitted": False,
        "link_text_emitted": False,
        "filenames_or_paths_emitted": False,
        "candidate_catalogue_blob_contents_read": False,
        "cmn_scientific_value_access": False,
        "cmn_event_identifier_access": False,
        "cmn_shower_label_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "external_validation_performed": False,
    }

    passed = all(
        [
            actual_commit == COMMIT,
            parser.cue_found,
            len(structural_candidates) >= 1,
            len(resolved) >= 1,
            bool(selected_path_sha256),
            bool(selected_blob_sha),
        ]
    )
    result["verdict"] = "PASS_CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT" if passed else "FAIL_CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT"

    out = a.output / "CMN_OFFICIAL_GITHUB_MIRROR_STRUCTURE_AUDIT_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
