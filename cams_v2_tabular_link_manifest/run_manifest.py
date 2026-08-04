#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse

import requests

PAGES = {
    "v2016": "https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html",
    "v2020": "https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html",
}
TABULAR = (
    "CAMS_California_v2.xlsx",
    "CAMS_BeNeLux_v2.xlsx",
    "CAMS_California_v2.1l",
    "CAMS_BeNeLux_v2.1l",
    "CAMS_by_date_v2.1l",
)


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.anchors: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self.current_href = dict(attrs).get("href")
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current_href is not None:
            self.anchors.append(
                {"href": self.current_href.strip(), "text": " ".join("".join(self.current_text).split())}
            )
            self.current_href = None
            self.current_text = []


def basename(href: str) -> str:
    return PurePosixPath(unquote(urlparse(href).path)).name


def build_result() -> dict:
    session = requests.Session()
    pages = {}
    for key, url in PAGES.items():
        response = session.get(url, timeout=300, allow_redirects=True)
        response.raise_for_status()
        raw = response.content
        parser = AnchorParser()
        parser.feed(raw.decode("latin-1"))
        tabular = {
            name: [
                {"href": a["href"], "resolved_url": urljoin(response.url, a["href"])}
                for a in parser.anchors
                if basename(a["href"]) == name
            ]
            for name in TABULAR
        }
        here = [
            {
                "href": a["href"],
                "resolved_url": urljoin(response.url, a["href"]),
                "basename": basename(a["href"]),
                "text": a["text"],
            }
            for a in parser.anchors
            if " ".join(a["text"].split()).casefold() == "here"
        ]
        pages[key] = {
            "requested_url": url,
            "final_url": response.url,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "tabular_links": tabular,
            "here_links": here,
        }

    exact_tabular = all(
        len(pages[key]["tabular_links"][name]) == 1 for key in PAGES for name in TABULAR
    )
    exact_here = all(len(pages[key]["here_links"]) == 1 for key in PAGES)
    same_doc = exact_here and (
        pages["v2016"]["here_links"][0]["basename"]
        == pages["v2020"]["here_links"][0]["basename"]
    )
    gates = {
        "both_pages_retrieved": len(pages) == 2,
        "exact_one_link_for_each_tabular_resource": exact_tabular,
        "exact_one_visible_here_anchor_per_page": exact_here,
        "documentation_basename_identical_across_pages": same_doc,
        "discovered_resources_not_requested": True,
        "meteor_values_not_read": True,
        "reserved_panels_not_read": True,
    }
    verdict = "PASS_CAMSV2_TABULAR_LINK_MANIFEST" if all(gates.values()) else "KILL_CAMSV2_TABULAR_LINK_MANIFEST"
    return {
        "method": "CAMS Database 2.0 official page-link manifest",
        "pages": pages,
        "resource_urls_requested": list(PAGES.values()),
        "discovered_resources_requested": False,
        "meteor_values_read": False,
        "label_values_read": False,
        "reserved_panels_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    try:
        result = build_result()
    except Exception as exc:
        result = {
            "method": "CAMS Database 2.0 official page-link manifest",
            "error": f"{type(exc).__name__}: {exc}",
            "discovered_resources_requested": False,
            "meteor_values_read": False,
            "label_values_read": False,
            "reserved_panels_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_CAMSV2_TABULAR_LINK_MANIFEST",
        }
    (out / "tabular_link_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    here = {
        key: value.get("here_links") for key, value in result.get("pages", {}).items()
    }
    (out / "RESULT.md").write_text(
        "# CAMS Database 2.0 tabular page-link manifest\n\n"
        f"**Verdict:** `{result['verdict']}`\n\n"
        f"- documentation anchors: `{here}`\n\n"
        + "\n".join(f"- {name}: {passed}" for name, passed in result.get("gates", {}).items())
        + "\n\nNo discovered resource was requested or opened.\n"
    )
    print(json.dumps({"verdict": result["verdict"], "here_links": here, "gates": result.get("gates"), "error": result.get("error")}, indent=2))
    if result["verdict"] != "PASS_CAMSV2_TABULAR_LINK_MANIFEST":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
