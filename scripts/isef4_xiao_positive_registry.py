#!/usr/bin/env python3
"""Parse all 41 originally published Xiao 2025 event annotations.

Primary evidence: unmodified Word Supplement Tables S1/S2 for site coordinates,
and Supplement Table S3 for exact figure-panel EDR IDs. No ungrounded pairing.
"""
from __future__ import annotations
import datetime as dt
import json
import re
from pathlib import Path

SOURCE=Path("diagnostics/isef4_original_xiao_workbook_inventory.json")
DEST=Path("diagnostics/isef4_xiao_41_published_event_registry.json")
PRODUCT=re.compile(r"^M\d{8,13}[A-Z]{0,4}$", re.I)
FIGURE=re.compile(r"(?i)^Supplementary\s+Fig\.?\s*S(\d+)\.")
COORD=re.compile(r"(\d{1,3}(?:\.\d+)?)\s*°\s*([NS])|(\d{1,3}(?:\.\d+)?)\s*°\s*([EW])",re.I)
PANEL=re.compile(r"^([0-9]{1,3})([a-z])$",re.I)

def parsed_coordinates(text: str) -> list[tuple[float,float]]:
    """Extract adjacent signed latitude and longitude tokens from a caption."""
    parts=[]
    for match in COORD.finditer(text):
        if match.group(1) is not None:
            parts.append(("latitude",float(match.group(1))*(-1 if match.group(2).upper()=="S" else 1)))
        if match.group(3) is not None:
            parts.append(("longitude",float(match.group(3))*(-1 if match.group(4).upper()=="W" else 1)))
    return [(a[1],b[1]) for a,b in zip(parts,parts[1:])
            if a[0]=="latitude" and b[0]=="longitude"]

def date_iso(raw:str)->str:
    # The ORIGINAL Word tables contain two "2018//7/26" tokens, one in
    # each attribution table. Collapse redundant slashes but preserve
    # source text and a visible anomaly field in every derived event.
    normalized=re.sub(r"/+","/",raw)
    if normalized.count("/")!=2:
        raise ValueError("uninterpretable source date: "+repr(raw))
    return dt.datetime.strptime(normalized,"%Y/%m/%d").date().isoformat()

def main()->None:
    source=json.loads(SOURCE.read_text().replace("\\n",""))
    audit=source["original_docx_structure_audit"]
    tabs=audit["table_structures"]
    if len(tabs)!=3 or [x["row_count"] for x in tabs]!=[13,30,70]:
        raise RuntimeError("original supplemental table layout changed; re-review source")
    if tabs[0]["all_original_rows"][0][:3]!=["No.","Terrain Name","Stratigraphic Age"]:
        raise RuntimeError("impact event table header changed")
    if tabs[1]["all_original_rows"][0][:3]!=["No.","Terrain Name","Stratigraphic Age"]:
        raise RuntimeError("endogenous event table header changed")
    if tabs[2]["all_original_rows"][0][:2]!=["Figure number","Data ID"]:
        raise RuntimeError("source image crosswalk heading changed")
    captions={}
    for entry in audit["original_supplementary_figure_captions"]:
        m=FIGURE.match(entry["text"])
        if not m:continue
        number=int(m.group(1))
        if number in captions:raise RuntimeError(f"duplicate Figure S{number} caption")
        captions[number]={"caption":entry["text"],"coords":parsed_coordinates(entry["text"]),
                          "paragraph_index":entry["paragraph_index"]}
    source_row_section=False
    figures={}
    for row_index,row in enumerate(tabs[2]["all_original_rows"]):
        if row and "Supplementary Figs." in row[0]:
            source_row_section=True
            continue
        if not source_row_section:continue
        for col in (0,2,4):
            if col+1>=len(row):continue
            marker=PANEL.fullmatch(row[col].strip())
            if not marker:continue
            num=int(marker.group(1));letter=marker.group(2).lower()
            key=f"{num}{letter}"
            if key in figures:
                raise RuntimeError(f"duplicate source table panel {key}")
            figures[key]={"data_id":row[col+1],"source_table_3_row":row_index+1,
                          "source_table_3_column":col+1}
    if len(captions)<35:
        raise RuntimeError("too few original supplementary captions; index incomplete")
    all_events=[]
    for table_no, label, expected in (
        (0,"impact_associated_in_paper",12),
        (1,"endogenic_attributed_in_paper",29),
    ):
        entries=tabs[table_no]["all_original_rows"][1:]
        if len(entries)!=expected:raise RuntimeError("original annotation count shifted")
        last_name=last_age=None
        for row_number,row in enumerate(entries,start=2):
            if len(row)!=8:raise RuntimeError("unexpected event-table columns")
            serial,name,age,lat,lon,before,after,slope=row
            if name.strip():last_name=name.strip()
            if age.strip():last_age=age.strip()
            if not last_name or not last_age:raise RuntimeError("unfillable source name/age")
            latitude=float(lat);longitude=float(lon)
            prior=date_iso(before);later=date_iso(after)
            if prior>=later:raise RuntimeError(f"nonchronological positive site {table_no}:{serial}")
            cand=[]
            for figure_num,figure in sorted(captions.items()):
                if any(abs(latitude-x)<0.00051 and abs(longitude-y)<0.00051
                       for x,y in figure["coords"]):
                    cand.append(figure_num)
            evidence=[]
            for number in cand:
                before_item=figures.get(f"{number}a")
                after_item=figures.get(f"{number}b")
                pair=None
                if before_item is not None and after_item is not None:
                    b=before_item["data_id"];a=after_item["data_id"]
                    if PRODUCT.fullmatch(b) and PRODUCT.fullmatch(a):
                        pair={"before_edr":b,"after_edr":a,
                              "source_before_panel":f"{number}a",
                              "source_after_panel":f"{number}b",
                              "source_before_table_row":before_item["source_table_3_row"],
                              "source_after_table_row":after_item["source_table_3_row"]}
                evidence.append({
                    "supplementary_figure":number,
                    "figure_caption_source_paragraph":captions[number]["paragraph_index"],
                    "figure_image_pair":pair,
                    "pair_status":"exact_two_EDR_panels" if pair else "no_unique_direct_two_EDR_panels",
                })
            all_events.append({
                "published_event_identifier":f"xiao2025-table{table_no+1}-row{serial}",
                "original_word_table_number":table_no+1,
                "original_word_excel_like_row":row_number,
                "source_number":serial,
                "source_attributed_mechanism":label,
                "terrain_name_source_fill_down":last_name,
                "stratigraphic_age_source_fill_down":last_age,
                "latitude_deg":latitude,
                "longitude_deg_east_signed":longitude,
                "before_date":prior,
                "after_date":later,
                "original_date_strings":[before,after],
                "source_date_slash_typography_corrected":(
                    before!=re.sub(r"/+","/",before)
                    or after!=re.sub(r"/+","/",after)
                ),
                "slope_deg":float(slope),
                "same_coordinate_figure_candidates":evidence,
                "site_polygon_known":False,
                "source_text_coordinates_precision":"published table decimals; not subpixel object centroid",
            })
    gambart=[x for x in all_events if x["terrain_name_source_fill_down"]=="Gambart C"]
    if len(gambart)!=1:raise RuntimeError("Gambart C event source lost")
    g=gambart[0]
    if (g["latitude_deg"],g["longitude_deg_east_signed"])!=(3.218,-11.908):
        raise RuntimeError("Gambart C published coordinate mismatch")
    links=[i["figure_image_pair"] for i in g["same_coordinate_figure_candidates"]
           if i["supplementary_figure"]==5]
    if links!=[{"before_edr":"M1138987659LE","after_edr":"M1200206882LE",
                "source_before_panel":"5a","source_after_panel":"5b",
                "source_before_table_row":12,"source_after_table_row":12}]:
        # Position within Table S3 may change without scientific ID changing;
        # fail visibly rather than relaxing identifiers.
        if len(links)!=1 or links[0] is None or (
            links[0]["before_edr"],links[0]["after_edr"])!=(
                "M1138987659LE","M1200206882LE"):
            raise RuntimeError("Gambart C exact S5 image ID crosswalk mismatch")
    out={
        "schema_version":"xiao2025-published-41-event-source-registry-v1",
        "paper_doi":"10.1093/nsr/nwaf384",
        "original_docx_sha256":audit["source_docx_sha256"],
        "source_table_1_impact_associated_count":12,
        "source_table_2_endogenic_attributed_count":29,
        "event_count":len(all_events),
        "figure_caption_count":len(captions),
        "figure_EDR_panel_count":sum(PRODUCT.fullmatch(item["data_id"]) is not None
                                     for item in figures.values()),
        "event_count_with_one_exact_matched_figure_EDR_pair":sum(
            len([e for e in item["same_coordinate_figure_candidates"]
                 if e["figure_image_pair"] is not None])==1
            for item in all_events
        ),
        "gambart_c_source_identifier":g["published_event_identifier"],
        "events":all_events,
        "interpretation":"Published development positives only; source mechanism attribution not independently verified. Membership in XLSX 568-pair table is not assumed. Coordinates are not precise polygons or detection outcomes.",
    }
    if len(all_events)!=41:raise RuntimeError("expected 41 primary-source event sites")
    DEST.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="events"},indent=2),flush=True)
    print("UNRESOLVED_EVENTS",json.dumps([
        {"source_id":e["published_event_identifier"],
         "name":e["terrain_name_source_fill_down"],
         "lat":e["latitude_deg"],"lon":e["longitude_deg_east_signed"],
         "figure_candidates":e["same_coordinate_figure_candidates"]}
        for e in all_events if not any(v["figure_image_pair"] is not None
                             for v in e["same_coordinate_figure_candidates"])
    ],indent=2),flush=True)

if __name__=="__main__":
    main()
