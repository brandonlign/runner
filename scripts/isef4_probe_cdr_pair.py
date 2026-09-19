#!/usr/bin/env python3
"""Find authoritative LROC CDR counterparts for the exact published S5 EDRs.

Metadata-only HTTP range probes. Calibrated I/F products could avoid a large
ISIS LROC local calibration kernel tree but cannot replace proper geometry,
photometric matching, image-registration or real event validation.
"""
from __future__ import annotations
import concurrent.futures
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT="https://pds.lroc.im-ldi.com/data/LRO-L-LROC-3-CDR-V1.0/"
PRODUCTS={
    "before":{"edr":"M1138987659LE","cdr":"M1138987659LC",
              "volume":"LROLRC_1017","doy":"2013317"},
    "after":{"edr":"M1200206882LE","cdr":"M1200206882LC",
             "volume":"LROLRC_1025","doy":"2015296"},
}
OUT=Path("diagnostics/isef4_gambart_exact_pds_cdr_pair_probe.json")
FIELDS=(
    "PDS_VERSION_ID","RECORD_TYPE","RECORD_BYTES","FILE_RECORDS",
    "LABEL_RECORDS","^IMAGE","^IMAGE_HEADER",
    "PRODUCT_ID","PRODUCT_CREATION_TIME","DATA_SET_ID",
    "INSTRUMENT_ID","INSTRUMENT_NAME","PRODUCT_TYPE","MISSION_PHASE_NAME",
    "START_TIME","STOP_TIME","LINES","LINE_SAMPLES","SAMPLE_BITS",
    "SAMPLE_TYPE","SCALING_FACTOR","OFFSET","BAND_STORAGE_TYPE",
    "SAMPLE_DISPLAY_DIRECTION","LINE_DISPLAY_DIRECTION","LINE_PREFIX_BYTES",
    "LINE_SUFFIX_BYTES","RADIANCE_SCALING_FACTOR","RADIANCE_OFFSET",
    "REFLECTANCE_SCALING_FACTOR","REFLECTANCE_OFFSET",
    "VALID_MINIMUM","VALID_MAXIMUM","MISSING_CONSTANT","INVALID_CONSTANT",
    "CORE_NULL","CORE_LOW_REPR_SATURATION","CORE_HIGH_REPR_SATURATION",
    "NULL","LOW_REPR_SATURATION","HIGH_REPR_SATURATION",
)
def probe(role, phase):
    rec=PRODUCTS[role]
    url=f"{ROOT}{rec['volume']}/DATA/{phase}/{rec['doy']}/NAC/{rec['cdr']}.IMG"
    req=urllib.request.Request(url,headers={
        "Range":"bytes=0-8191",
        "User-Agent":"LUNARSHIFT-exact-original-PDS-CDR-metadata-probe/1.0",
    })
    try:
        with urllib.request.urlopen(req,timeout=22) as response:
            status=response.status
            cr=response.headers.get("Content-Range")
            body=response.read(8192)
            mime=response.headers.get("Content-Type")
        record={"source_role":role,"url":url,"status":status,
                "content_range":cr,"content_type":mime,"probe_bytes":len(body)}
        if status!=206 or cr is None:
            record["verification"]="no_verified_PDS_byte_range"
            return record
        m=re.fullmatch(r"bytes 0-(\d+)/(\d+)",cr)
        if m is None or int(m.group(1))!=8191 or len(body)!=8192:
            record["verification"]="invalid_source_range"
            return record
        label=body.decode("ascii",errors="replace")
        values={}
        for key in FIELDS:
            found=re.search(r"(?m)^\s*"+key+r"\s*=\s*(.+)$",label)
            if found:values[key]=found.group(1).strip()[:180]
        # Record the exact PDS label even when the label uses a different
        # product-key convention than the public filename.
        record.update(full_image_bytes=int(m.group(2)),pds_fields=values,
                      first_120_PDS_characters=label[:120],
                      verification=(
                          "verified_CDR_PDS3_source_header"
                          if "PDS_VERSION_ID" in values and (
                              rec["cdr"] in label or rec["edr"] in label)
                          else "PDS3_header_found_but_exact_image_reference_unverified"
                      ))
        return record
    except urllib.error.HTTPError as exc:
        return {"source_role":role,"url":url,"http_status":exc.code,
                "verification":"http_error"}
    except Exception as exc:
        return {"source_role":role,"url":url,"verification":"probe_error",
                "error":type(exc).__name__+": "+str(exc)[:200]}

def main():
    cases=[(role,phase) for role in PRODUCTS for phase in ("ESM","ESM2","ESM3")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(lambda case:probe(*case),cases))
    selected={}
    for role in PRODUCTS:
        good=[x for x in results if
              x["source_role"]==role and
              x["verification"]=="verified_CDR_PDS3_source_header"]
        selected[role]=good
    record={
        "schema_version":"gambart-exact-LROC-CDR-counterpart-source-v1",
        "input_published_EDRs":[PRODUCTS[r]["edr"] for r in PRODUCTS],
        "expected_CDRs":[PRODUCTS[r]["cdr"] for r in PRODUCTS],
        "verified_matches":selected,
        "probes":results,
        "CDR_scientific_role":"NASA calibrated NAC I/F counterpart; not independently geolocated change",
        "input_reference":"Xiao et al. 2025 original supplementary Figure S5 and Table S3",
    }
    OUT.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record,indent=2),flush=True)
    if any(len(selected[role])!=1 for role in PRODUCTS):
        raise RuntimeError("no unique metadata-verified CDR counterpart for each epoch")

if __name__=="__main__":
    main()
