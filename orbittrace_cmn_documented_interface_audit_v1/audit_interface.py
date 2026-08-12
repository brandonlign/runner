#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

INITIAL_URL = "http://cmn.rgn.hr/downloads/downloads.html"
HOST = "cmn.rgn.hr"
PATH = "/downloads/downloads.html"
ALLOWED_EXTENSIONS = {"zip", "csv", "txt", "dat"}
KEYWORDS = ("orbit", "catalog", "data", "download", "query", "search")
REDIRECT_CODES = {301, 302, 307, 308}
OUT = Path("output")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, Any]] = []
        self.current_form: dict[str, Any] | None = None
        self.candidate_extensions: Counter[str] = Counter()
        self.candidate_count = 0
        self.relevant_counts: Counter[str] = Counter()
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {str(k): ("" if v is None else str(v)) for k, v in attrs}
        if tag == "form":
            action = a.get("action", "")
            parsed = urllib.parse.urlparse(action)
            entry = {
                "action_path": parsed.path or "",
                "method": a.get("method", "").lower(),
                "fields": [],
            }
            self.forms.append(entry)
            self.current_form = entry
        elif tag in {"input", "select", "button", "textarea"} and self.current_form is not None:
            name = a.get("name", "")
            typ = a.get("type", tag).lower()
            if name or tag in {"select", "button"}:
                self.current_form["fields"].append({"tag": tag, "name": name, "type": typ})
        elif tag == "a":
            self._href = a.get("href", "")
            self._link_text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.current_form = None
            return
        if tag != "a" or self._href is None:
            return

        href = self._href
        text = " ".join("".join(self._link_text).split())
        parsed = urllib.parse.urlparse(href)
        link_host = (parsed.hostname or "").lower()
        same_or_relative = not parsed.netloc or link_host == HOST
        suffix = Path(parsed.path).suffix.lower().lstrip(".")
        if same_or_relative and suffix in ALLOWED_EXTENSIONS:
            self.candidate_count += 1
            self.candidate_extensions[suffix] += 1

        searchable = f"{parsed.path} {text}".lower()
        for keyword in KEYWORDS:
            if keyword in searchable:
                self.relevant_counts[keyword] += 1

        self._href = None
        self._link_text = []


def req(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def request_once(opener: urllib.request.OpenerDirector, url: str) -> tuple[int, str, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "OrbitTrace-CMN-documented-interface-audit-v1/1.0"})
    try:
        with opener.open(request, timeout=30) as response:
            return int(response.status), response.geturl(), dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), url, dict(exc.headers.items()) if exc.headers else {}, exc.read()


def valid_https_only_redirect(location: str) -> str | None:
    absolute = urllib.parse.urljoin(INITIAL_URL, location)
    p = urllib.parse.urlparse(absolute)
    if (
        p.scheme.lower() == "https"
        and (p.hostname or "").lower() == HOST
        and (p.path or "") == PATH
        and not p.query
        and not p.params
        and not p.fragment
    ):
        return absolute
    return None


def main() -> int:
    freshness = Path("orbittrace_cmn_zero_data_freshness_audit_v1/RESULT.md")
    iau_fail = Path("orbittrace_cmn_interface_structure_audit_v1/RESULT.md")
    req(freshness.is_file() and "PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT" in freshness.read_text(), "binding CMN freshness PASS missing")
    req(iau_fail.is_file() and "FAIL_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT" in iau_fail.read_text(), "binding IAU CMN interface FAIL missing")

    parsed_initial = urllib.parse.urlparse(INITIAL_URL)
    req(parsed_initial.scheme == "http" and parsed_initial.hostname == HOST and parsed_initial.path == PATH and not parsed_initial.query, "initial URL changed")

    opener = urllib.request.build_opener(NoRedirect)
    request_count = 1
    status, final_url, headers, raw = request_once(opener, INITIAL_URL)
    redirect_rule_satisfied = True
    redirect_used = False

    if status in REDIRECT_CODES:
        location = headers.get("Location") or headers.get("location") or ""
        target = valid_https_only_redirect(location)
        if target is None:
            redirect_rule_satisfied = False
        else:
            redirect_used = True
            request_count = 2
            status, final_url, headers, raw = request_once(opener, target)
            if status in REDIRECT_CODES:
                redirect_rule_satisfied = False

    parsed_final = urllib.parse.urlparse(final_url)
    content_type = (headers.get("Content-Type") or headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    text = raw.decode("utf-8", errors="replace")
    cmn_present = bool(re.search(r"Croatian\s+Meteor\s+Network|\bCMN\b", text, re.I))

    parser = StructureParser()
    parser.feed(text)

    result: dict[str, Any] = {
        "stage": "CMN_DOCUMENTED_INTERFACE_AUDIT_V1",
        "request_count": request_count,
        "redirect_used": redirect_used,
        "redirect_rule_satisfied": redirect_rule_satisfied,
        "status": status,
        "final_scheme": parsed_final.scheme.lower(),
        "final_host": (parsed_final.hostname or "").lower(),
        "final_path": parsed_final.path or "",
        "final_query_empty": not bool(parsed_final.query),
        "content_type": content_type,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "cmn_source_label_present": cmn_present,
        "form_count": len(parser.forms),
        "forms": parser.forms,
        "candidate_download_link_count": int(parser.candidate_count),
        "candidate_extension_counts": {ext: int(parser.candidate_extensions.get(ext, 0)) for ext in sorted(ALLOWED_EXTENSIONS)},
        "candidate_download_structurally_present": bool(parser.candidate_count > 0),
        "relevant_link_category_counts": {key: int(parser.relevant_counts.get(key, 0)) for key in KEYWORDS},
        "page_links_followed": False,
        "candidate_files_downloaded": False,
        "raw_html_emitted": False,
        "filenames_emitted": False,
        "scientific_row_values_emitted": False,
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
            redirect_rule_satisfied,
            request_count <= 2,
            status == 200,
            result["final_host"] == HOST,
            result["final_path"] == PATH,
            result["final_query_empty"],
            "html" in content_type,
            cmn_present,
            result["candidate_download_structurally_present"],
        ]
    )
    result["verdict"] = "PASS_CMN_DOCUMENTED_INTERFACE_AUDIT" if passed else "FAIL_CMN_DOCUMENTED_INTERFACE_AUDIT"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "CMN_DOCUMENTED_INTERFACE_AUDIT_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
