#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL="https://ceres.ta3.sk/"
HOST="ceres.ta3.sk"
OUT=Path("output")
KEYWORDS=("orbit","catalog","data","download","query","search")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]; self.current_form=None
        self.links=[]; self._link=None; self._text=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="form":
            action=a.get("action","")
            p=urllib.parse.urlparse(action)
            entry={"action_path":p.path or "", "method":a.get("method","").lower(), "fields":[]}
            self.forms.append(entry); self.current_form=entry
        elif tag in {"input","select","button","textarea"} and self.current_form is not None:
            name=a.get("name","")
            typ=a.get("type",tag).lower()
            if name or tag in {"select","button"}:
                self.current_form["fields"].append({"tag":tag,"name":name,"type":typ})
        elif tag=="a":
            self._link=a.get("href",""); self._text=[]
    def handle_data(self,data):
        if self._link is not None: self._text.append(data)
    def handle_endtag(self,tag):
        if tag=="form": self.current_form=None
        elif tag=="a" and self._link is not None:
            href=self._link; text=" ".join("".join(self._text).split()).lower()
            parsed=urllib.parse.urlparse(href)
            path=parsed.path or ""
            blob=(path+" "+text).lower()
            cats=[k for k in KEYWORDS if k in blob]
            if cats:
                self.links.append({"path":path,"categories":cats})
            self._link=None; self._text=[]

def main()->int:
    prior=Path("orbittrace_cmn_zero_data_freshness_audit_v1/RESULT.md")
    if not prior.is_file() or "PASS_CMN_ZERO_DATA_REPO_FRESHNESS_AUDIT" not in prior.read_text():
        raise RuntimeError("binding CMN freshness PASS missing")
    req=urllib.request.Request(URL,headers={"User-Agent":"OrbitTrace-CMN-structure-audit-v1/1.0"})
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req,timeout=30) as r:
            status=int(r.status); final_url=r.geturl(); ctype=r.headers.get("Content-Type",""); raw=r.read()
    except urllib.error.HTTPError as e:
        status=int(e.code); final_url=URL; ctype=e.headers.get("Content-Type","") if e.headers else ""; raw=e.read()
    text=raw.decode("utf-8",errors="replace")
    parsed_url=urllib.parse.urlparse(final_url)
    cmn_present=bool(re.search(r"Croatian\s+Meteor\s+Network|\bCMN\b",text,re.I))
    parser=StructureParser(); parser.feed(text)
    structural_control=bool(parser.forms or parser.links)
    result={
        "stage":"CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT_V1",
        "status":status,
        "final_scheme":parsed_url.scheme,
        "final_host":parsed_url.hostname,
        "content_type":ctype.split(";",1)[0].strip().lower(),
        "response_sha256":hashlib.sha256(raw).hexdigest(),
        "cmn_source_label_present":cmn_present,
        "form_count":len(parser.forms),
        "forms":parser.forms,
        "relevant_links":parser.links,
        "structural_query_or_data_control_present":structural_control,
        "network_fetch_count":1,
        "links_followed":False,
        "forms_submitted":False,
        "raw_html_emitted":False,
        "scientific_row_values_emitted":False,
        "cmn_scientific_value_access":False,
        "cmn_event_identifier_access":False,
        "cmn_shower_label_access":False,
        "target_information_access":False,
        "target_region_events_accessed":False,
        "sonotaco_scientific_access":False,
        "maarsy_scientific_access":False,
        "dms_scientific_access":False,
    }
    passed=(status==200 and parsed_url.scheme=="https" and parsed_url.hostname==HOST and "html" in result["content_type"] and cmn_present and structural_control)
    result["verdict"]="PASS_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT" if passed else "FAIL_CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT"
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"CMN_PUBLIC_INTERFACE_STRUCTURE_AUDIT_V1.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if passed else 1

if __name__=="__main__": raise SystemExit(main())
